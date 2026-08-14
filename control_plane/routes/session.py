"""Session evidence and event-sourced runtime state routes."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

from control_plane.repository import replay_session_ledger, store_evidence_batch
from shared.forensic_ledger import append_receipt, list_receipts
from shared.models import (
    RuntimeAgentRecord,
    RuntimeStateDeltaEvent,
    RuntimeStateEventListResponse,
    RuntimeStateMutationRequest,
    RuntimeStateMutationResponse,
    RuntimeStateSnapshot,
    RuntimeStateSummary,
    RuntimeTaskRecord,
    SessionEvidenceRequest,
    SessionEvidenceResponse,
    SessionLedgerReplayResponse,
)
from shared.runtime_paths import default_session_ledger_path

router = APIRouter(tags=["session"])
LEDGER_DB_PATH = Path(
    os.environ.get("SESSION_LEDGER_DB_PATH", str(default_session_ledger_path()))
).expanduser()
RUNTIME_RECEIPT = "runtime_state_event"


@router.post("/session/evidence", response_model=SessionEvidenceResponse)
def ingest_evidence(req: SessionEvidenceRequest):
    return SessionEvidenceResponse(status="ok", **store_evidence_batch(req))


@router.get("/session/{session_id}/replay-ledger", response_model=SessionLedgerReplayResponse)
def replay_ledger(session_id: str):
    return replay_session_ledger(session_id)


def _auth(authorization: str | None) -> None:
    expected = os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid_bearer_token")


def _event(row: dict[str, Any]) -> dict[str, Any]:
    payload = (
        json.loads(row.get("payload") or "{}")
        if isinstance(row.get("payload"), str)
        else row.get("payload") or {}
    )
    cmd = (
        json.loads(row.get("cmd_vector") or "{}")
        if isinstance(row.get("cmd_vector"), str)
        else row.get("cmd_vector") or {}
    )
    return {
        "seq": int(row["logical_clock"]),
        "state_hash": row["state_hash"],
        "accepted_at": row["created_at"],
        "event_type": payload.get("event_type"),
        "payload": payload.get("payload") or {},
        "idempotency_key": cmd.get("idempotency_key", ""),
    }


def _snapshot(session_id: str) -> RuntimeStateSnapshot:
    agents = {}
    tasks = {}
    last_seq = 0
    last_hash = "sha256:0"

    for row in list_receipts(
        LEDGER_DB_PATH,
        session_id,
        after_logical_clock=0,
        receipt_type=RUNTIME_RECEIPT,
    ):
        event = _event(row)
        last_seq = event["seq"]
        last_hash = event["state_hash"]
        accepted_at = datetime.fromisoformat(str(event["accepted_at"]).replace("Z", "+00:00"))
        payload = event["payload"]

        if event["event_type"] == "agent_upsert":
            agents[payload["agent_id"]] = RuntimeAgentRecord(
                agent_id=payload["agent_id"],
                display_name=payload.get("display_name") or payload["agent_id"],
                runtime=payload["runtime"],
                host=payload.get("host") or "unknown",
                branch=payload.get("branch") or "unknown",
                commit_hash=payload.get("commit_hash") or "unknown",
                dirty=bool(payload.get("dirty", False)),
                note=payload.get("note", ""),
                last_seen_at=accepted_at,
            )
        elif event["event_type"] == "task_upsert":
            previous = tasks.get(payload["task_id"])
            tasks[payload["task_id"]] = RuntimeTaskRecord(
                task_id=payload["task_id"],
                title=payload.get("title") or payload["task_id"],
                state=payload["state"],
                assigned_agent=previous.assigned_agent if previous else None,
                source=payload.get("source", ""),
                note=payload.get("note", ""),
                updated_by=payload.get("updated_by", "operator"),
                updated_at=accepted_at,
            )
        elif event["event_type"] == "assignment_upsert" and payload["task_id"] in tasks:
            tasks[payload["task_id"]].assigned_agent = payload.get("agent_id")
            tasks[payload["task_id"]].updated_at = accepted_at
        elif event["event_type"] == "heartbeat" and payload["agent_id"] in agents:
            agents[payload["agent_id"]].last_seen_at = accepted_at

    return RuntimeStateSnapshot(
        session_id=session_id,
        generated_at=datetime.now(UTC),
        last_seq=last_seq,
        last_state_hash=last_hash,
        summary=RuntimeStateSummary(
            agent_count=len(agents),
            runtime_counts={
                runtime: sum(agent.runtime == runtime for agent in agents.values())
                for runtime in ("local", "worktree", "cloud")
            },
            task_counts={
                state: sum(task.state == state for task in tasks.values())
                for state in ("queued", "running", "blocked", "done")
            },
        ),
        agents=agents,
        tasks=tasks,
    )


@router.get("/runtime-state/snapshot", response_model=RuntimeStateSnapshot)
def runtime_state_snapshot(
    session_id: str = Query(..., min_length=1),
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    return _snapshot(session_id)


@router.get("/runtime-state/events", response_model=RuntimeStateEventListResponse)
def runtime_state_events(
    session_id: str = Query(..., min_length=1),
    after_seq: int = Query(0, ge=0),
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    events = [
        _event(row)
        for row in list_receipts(
            LEDGER_DB_PATH,
            session_id,
            after_logical_clock=after_seq,
            receipt_type=RUNTIME_RECEIPT,
        )
    ]
    return RuntimeStateEventListResponse(
        session_id=session_id,
        events=[
            RuntimeStateDeltaEvent(
                seq=event["seq"],
                state_hash=event["state_hash"],
                idempotency_key=event["idempotency_key"],
                event_type=event["event_type"],
                payload=event["payload"],
                accepted_at=datetime.fromisoformat(
                    str(event["accepted_at"]).replace("Z", "+00:00")
                ),
            )
            for event in events
        ],
    )


@router.post("/runtime-state/events", response_model=RuntimeStateMutationResponse)
def runtime_state_append(
    request: RuntimeStateMutationRequest,
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    if request.event_type not in {
        "agent_upsert",
        "task_upsert",
        "assignment_upsert",
        "heartbeat",
    }:
        raise HTTPException(status_code=422, detail="unsupported_event_type")

    for row in list_receipts(
        LEDGER_DB_PATH,
        request.session_id,
        receipt_type=RUNTIME_RECEIPT,
    ):
        event = _event(row)
        if event["idempotency_key"] == request.idempotency_key:
            return RuntimeStateMutationResponse(
                status="duplicate",
                session_id=request.session_id,
                applied_seq=event["seq"],
                state_hash=event["state_hash"],
                event_type=request.event_type,
            )

    result = append_receipt(
        LEDGER_DB_PATH,
        session_id=request.session_id,
        run_id=f"runtime-state-{request.session_id}",
        trace_id=request.idempotency_key,
        receipt_type=RUNTIME_RECEIPT,
        status="ACCEPTED",
        job_name="runtime_state_mutation",
        principal_id="runtime_state_operator",
        authz_scope="runtime-state:write",
        policy_version="rbac.v1",
        cmd_vector={
            "idempotency_key": request.idempotency_key,
            "event_type": request.event_type,
        },
        payload={
            "event_type": request.event_type,
            "payload": request.payload,
        },
    )
    return RuntimeStateMutationResponse(
        status="accepted",
        session_id=request.session_id,
        applied_seq=result.logical_clock,
        state_hash=result.state_hash,
        event_type=request.event_type,
    )
