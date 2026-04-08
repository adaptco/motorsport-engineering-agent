from __future__ import annotations

import asyncio
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from shared.forensic_ledger import append_receipt, list_receipts
from shared.models import (
    RuntimeAgentRecord,
    RuntimeAssignmentUpsertPayload,
    RuntimeHeartbeatPayload,
    RuntimeStateAgentUpsertEvent,
    RuntimeStateDeltaEvent,
    RuntimeStateEventListResponse,
    RuntimeStateMutationRequest,
    RuntimeStateMutationResponse,
    RuntimeStateSnapshot,
    RuntimeStateSummary,
    RuntimeStateTaskUpsertEvent,
    RuntimeTaskRecord,
)
from shared.runtime_paths import default_session_ledger_path

router = APIRouter(prefix="/runtime-state", tags=["runtime-state"])

RUNTIME_STATE_RECEIPT_TYPE = "runtime_state_event"
SESSION_LEDGER_DB_PATH = Path(os.environ.get("SESSION_LEDGER_DB_PATH", str(default_session_ledger_path()))).expanduser()
RUNTIME_STATE_SSE_HEARTBEAT_SECONDS = int(os.environ.get("RUNTIME_STATE_SSE_HEARTBEAT_SECONDS", "15"))
RUNTIME_STATE_MAX_REPLAY_EVENTS = int(os.environ.get("RUNTIME_STATE_MAX_REPLAY_EVENTS", "5000"))

COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _check_shared_token(authorization: str | None, access_token: str | None = None) -> None:
    expected = os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()
    if expected and authorization != f"Bearer {expected}" and access_token != expected:
        raise HTTPException(status_code=401, detail="invalid_bearer_token")


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_commit_hash(value: str | None) -> tuple[str, bool]:
    raw = (value or "").strip().lower()
    if not raw:
        return "unknown", False
    if COMMIT_RE.match(raw):
        return raw, False
    return "INVALID_HASH", True


def _coerce_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if event_type == "agent_upsert":
        event = RuntimeStateAgentUpsertEvent(event_type=event_type, payload=payload)
        data = event.model_dump(mode="json")
        normalized, invalid = _normalize_commit_hash(data["payload"].get("commit_hash"))
        data["payload"]["commit_hash"] = normalized
        data["payload"]["dirty"] = bool(data["payload"].get("dirty")) or invalid
        return data
    if event_type == "task_upsert":
        event = RuntimeStateTaskUpsertEvent(event_type=event_type, payload=payload)
        return event.model_dump(mode="json")
    if event_type == "assignment_upsert":
        event = RuntimeStateAssignmentUpsertPayload(**payload)
        return {"event_type": event_type, "payload": event.model_dump(mode="json")}
    if event_type == "heartbeat":
        event = RuntimeHeartbeatPayload(**payload)
        return {"event_type": event_type, "payload": event.model_dump(mode="json")}
    raise HTTPException(status_code=422, detail="unsupported_event_type")


@dataclass
class SnapshotCacheEntry:
    last_seq: int
    snapshot: RuntimeStateSnapshot


_SNAPSHOT_CACHE: dict[str, SnapshotCacheEntry] = {}


def _parse_receipt_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload_raw = row.get("payload") or "{}"
    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
    cmd_raw = row.get("cmd_vector") or "{}"
    cmd_vector = json.loads(cmd_raw) if isinstance(cmd_raw, str) else cmd_raw
    return {
        "seq": int(row["logical_clock"]),
        "state_hash": row["state_hash"],
        "accepted_at": row["created_at"],
        "event_type": payload.get("event_type"),
        "payload": payload.get("payload") or {},
        "idempotency_key": cmd_vector.get("idempotency_key", ""),
    }


def _materialize_snapshot(session_id: str) -> RuntimeStateSnapshot:
    cached = _SNAPSHOT_CACHE.get(session_id)
    if cached:
        latest_rows = list_receipts(
            SESSION_LEDGER_DB_PATH,
            session_id,
            after_logical_clock=cached.last_seq,
            receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
            limit=1,
        )
        if not latest_rows:
            return cached.snapshot

    rows = list_receipts(
        SESSION_LEDGER_DB_PATH,
        session_id,
        after_logical_clock=0,
        receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
    )
    agents: dict[str, RuntimeAgentRecord] = {}
    tasks: dict[str, RuntimeTaskRecord] = {}
    last_seq = 0
    last_state_hash = "sha256:0"

    for row in rows:
        parsed = _parse_receipt_payload(row)
        last_seq = parsed["seq"]
        last_state_hash = parsed["state_hash"]
        now = datetime.now(UTC)

        if parsed["event_type"] == "agent_upsert":
            payload = parsed["payload"]
            agent_id = payload["agent_id"]
            last_seen = datetime.fromisoformat(parsed["accepted_at"].replace("Z", "+00:00"))
            agents[agent_id] = RuntimeAgentRecord(
                agent_id=agent_id,
                display_name=payload.get("display_name") or agent_id,
                runtime=payload["runtime"],
                host=payload.get("host") or "unknown",
                branch=payload.get("branch") or "unknown",
                commit_hash=payload.get("commit_hash") or "unknown",
                dirty=bool(payload.get("dirty", False)),
                note=payload.get("note", ""),
                last_seen_at=last_seen,
            )
            continue

        if parsed["event_type"] == "task_upsert":
            payload = parsed["payload"]
            task_id = payload["task_id"]
            previous = tasks.get(task_id)
            assigned = previous.assigned_agent if previous else None
            tasks[task_id] = RuntimeTaskRecord(
                task_id=task_id,
                title=payload.get("title") or task_id,
                state=payload["state"],
                assigned_agent=assigned,
                source=payload.get("source", ""),
                note=payload.get("note", ""),
                updated_by=payload.get("updated_by", "operator"),
                updated_at=datetime.fromisoformat(parsed["accepted_at"].replace("Z", "+00:00")),
            )
            continue

        if parsed["event_type"] == "assignment_upsert":
            payload = parsed["payload"]
            task_id = payload["task_id"]
            task = tasks.get(task_id)
            if task is None:
                tasks[task_id] = RuntimeTaskRecord(
                    task_id=task_id,
                    title=task_id,
                    state="queued",
                    assigned_agent=payload.get("agent_id"),
                    source="",
                    note="",
                    updated_by=payload.get("updated_by", "operator"),
                    updated_at=datetime.fromisoformat(parsed["accepted_at"].replace("Z", "+00:00")),
                )
            else:
                task.assigned_agent = payload.get("agent_id")
                task.updated_by = payload.get("updated_by", "operator")
                task.updated_at = datetime.fromisoformat(parsed["accepted_at"].replace("Z", "+00:00"))
            continue

        if parsed["event_type"] == "heartbeat":
            payload = parsed["payload"]
            agent_id = payload["agent_id"]
            if agent_id in agents:
                at = payload.get("at") or parsed["accepted_at"]
                agents[agent_id].last_seen_at = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
            else:
                agents[agent_id] = RuntimeAgentRecord(
                    agent_id=agent_id,
                    display_name=agent_id,
                    runtime="local",
                    host="unknown",
                    branch="unknown",
                    commit_hash="unknown",
                    dirty=False,
                    note="",
                    last_seen_at=now,
                )

    summary = RuntimeStateSummary(
        agent_count=len(agents),
        runtime_counts={
            "local": sum(1 for agent in agents.values() if agent.runtime == "local"),
            "worktree": sum(1 for agent in agents.values() if agent.runtime == "worktree"),
            "cloud": sum(1 for agent in agents.values() if agent.runtime == "cloud"),
        },
        task_counts={
            "queued": sum(1 for task in tasks.values() if task.state == "queued"),
            "running": sum(1 for task in tasks.values() if task.state == "running"),
            "blocked": sum(1 for task in tasks.values() if task.state == "blocked"),
            "done": sum(1 for task in tasks.values() if task.state == "done"),
        },
    )
    snapshot = RuntimeStateSnapshot(
        session_id=session_id,
        generated_at=datetime.now(UTC),
        last_seq=last_seq,
        last_state_hash=last_state_hash,
        summary=summary,
        agents=agents,
        tasks=tasks,
    )
    _SNAPSHOT_CACHE[session_id] = SnapshotCacheEntry(last_seq=last_seq, snapshot=snapshot)
    return snapshot


class RuntimeStateHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers[session_id].add(queue)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            if session_id in self._subscribers:
                self._subscribers[session_id].discard(queue)
                if not self._subscribers[session_id]:
                    del self._subscribers[session_id]

    async def publish(self, session_id: str, event: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(session_id, set()))
        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(event)


_HUB = RuntimeStateHub()


def _sse_frame(*, event: str, payload: dict[str, Any], event_id: int | None = None) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(payload, separators=(',', ':'))}")
    return "\n".join(lines) + "\n\n"


def _sse_heartbeat() -> str:
    return ": ping\n\n"


def _receipt_rows_to_events(session_id: str, rows: list[dict[str, Any]]) -> RuntimeStateEventListResponse:
    events = [
        RuntimeStateDeltaEvent(
            seq=parsed["seq"],
            state_hash=parsed["state_hash"],
            idempotency_key=parsed["idempotency_key"],
            event_type=parsed["event_type"],
            payload=parsed["payload"],
            accepted_at=datetime.fromisoformat(str(parsed["accepted_at"]).replace("Z", "+00:00")),
        )
        for parsed in (_parse_receipt_payload(row) for row in rows)
    ]
    return RuntimeStateEventListResponse(session_id=session_id, events=events)


@router.get("/snapshot", response_model=RuntimeStateSnapshot)
def runtime_state_snapshot(
    session_id: str = Query(..., min_length=1),
    authorization: str | None = Header(default=None),
) -> RuntimeStateSnapshot:
    _check_shared_token(authorization)
    return _materialize_snapshot(session_id)


@router.get("/events", response_model=RuntimeStateEventListResponse)
def runtime_state_events(
    session_id: str = Query(..., min_length=1),
    after_seq: int = Query(default=0, ge=0),
    authorization: str | None = Header(default=None),
) -> RuntimeStateEventListResponse:
    _check_shared_token(authorization)
    rows = list_receipts(
        SESSION_LEDGER_DB_PATH,
        session_id,
        after_logical_clock=after_seq,
        receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
        limit=RUNTIME_STATE_MAX_REPLAY_EVENTS,
    )
    return _receipt_rows_to_events(session_id, rows)


@router.post("/events", response_model=RuntimeStateMutationResponse)
async def runtime_state_append_event(
    request: RuntimeStateMutationRequest,
    authorization: str | None = Header(default=None),
) -> RuntimeStateMutationResponse:
    _check_shared_token(authorization)
    normalized = _coerce_event(request.event_type, request.payload)
    rows = list_receipts(
        SESSION_LEDGER_DB_PATH,
        request.session_id,
        receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
    )
    for row in rows:
        cmd_vector = json.loads(row["cmd_vector"]) if isinstance(row["cmd_vector"], str) else row["cmd_vector"]
        if cmd_vector.get("idempotency_key") == request.idempotency_key:
            return RuntimeStateMutationResponse(
                status="duplicate",
                session_id=request.session_id,
                applied_seq=int(row["logical_clock"]),
                state_hash=row["state_hash"],
                event_type=request.event_type,
            )

    append_result = append_receipt(
        SESSION_LEDGER_DB_PATH,
        session_id=request.session_id,
        run_id=f"runtime-state-{request.session_id}",
        trace_id=request.idempotency_key,
        receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
        status="ACCEPTED",
        job_name="runtime_state_mutation",
        principal_id="runtime_state_operator",
        authz_scope="runtime-state:write",
        policy_version="rbac.v1",
        cmd_vector={
            "idempotency_key": request.idempotency_key,
            "event_type": request.event_type,
            "client_ts": request.client_ts.isoformat() if request.client_ts else _iso_now(),
        },
        payload=normalized,
    )
    _SNAPSHOT_CACHE.pop(request.session_id, None)

    committed = RuntimeStateDeltaEvent(
        seq=append_result.logical_clock,
        state_hash=append_result.state_hash,
        idempotency_key=request.idempotency_key,
        event_type=request.event_type,
        payload=normalized["payload"],
        accepted_at=datetime.now(UTC),
    )
    await _HUB.publish(request.session_id, committed.model_dump(mode="json"))
    return RuntimeStateMutationResponse(
        status="accepted",
        session_id=request.session_id,
        applied_seq=append_result.logical_clock,
        state_hash=append_result.state_hash,
        event_type=request.event_type,
    )


@router.get("/stream")
async def runtime_state_stream(
    request: Request,
    session_id: str = Query(..., min_length=1),
    after_seq: int = Query(default=0, ge=0),
    once: bool = Query(default=False),
    access_token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    _check_shared_token(authorization, access_token)

    effective_after = after_seq
    if last_event_id:
        try:
            effective_after = max(effective_after, int(last_event_id))
        except ValueError:
            pass

    queue = await _HUB.subscribe(session_id)

    async def event_stream():
        try:
            if effective_after > 0:
                backlog_rows = list_receipts(
                    SESSION_LEDGER_DB_PATH,
                    session_id,
                    after_logical_clock=effective_after,
                    receipt_type=RUNTIME_STATE_RECEIPT_TYPE,
                    limit=RUNTIME_STATE_MAX_REPLAY_EVENTS,
                )
                backlog = _receipt_rows_to_events(session_id, backlog_rows)
                for item in backlog.events:
                    payload = item.model_dump(mode="json")
                    yield _sse_frame(event="runtime_state", payload=payload, event_id=item.seq)
                if once:
                    return

            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=RUNTIME_STATE_SSE_HEARTBEAT_SECONDS)
                    yield _sse_frame(event="runtime_state", payload=item, event_id=int(item["seq"]))
                except TimeoutError:
                    yield _sse_heartbeat()
        finally:
            await _HUB.unsubscribe(session_id, queue)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
