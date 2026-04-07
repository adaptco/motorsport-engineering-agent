from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path(os.environ.get("A2A_WORKFLOW_STATE_DIR", ".mea_tmp/workflow_state"))
MAX_HISTORY = int(os.environ.get("A2A_WORKFLOW_STATE_MAX_HISTORY", "50"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(session_id: str, workflow_id: str) -> Path:
    safe_session = session_id.replace("/", "_")
    safe_workflow = workflow_id.replace("/", "_")
    return STATE_DIR / f"{safe_session}__{safe_workflow}.json"


def _history_path(session_id: str, workflow_id: str) -> Path:
    safe_session = session_id.replace("/", "_")
    safe_workflow = workflow_id.replace("/", "_")
    return STATE_DIR / "history" / f"{safe_session}__{safe_workflow}.jsonl"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_workflow_state(session_id: str, workflow_id: str) -> dict[str, Any] | None:
    path = _state_path(session_id, workflow_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("session_id") != session_id or data.get("workflow_id") != workflow_id:
        raise ValueError("Persisted workflow state identity mismatch")
    return data


def persist_workflow_state(state: dict[str, Any]) -> dict[str, Any]:
    session_id = str(state["session_id"])
    workflow_id = str(state["workflow_id"])
    path = _state_path(session_id, workflow_id)

    existing = load_workflow_state(session_id, workflow_id)
    version = 1 if not existing else int(existing.get("version", 0)) + 1

    payload = dict(state)
    payload.setdefault("created_at", existing.get("created_at") if existing else _utc_now())
    payload["version"] = version
    payload["updated_at"] = _utc_now()

    _atomic_write(path, payload)
    _append_history(payload)
    _prune_history(session_id, workflow_id)
    return payload


def advance_workflow_position(
    *,
    session_id: str,
    workflow_id: str,
    current_position: str,
    status: str,
    summary: str | None = None,
    pending_actions: list[str] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    trace_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = load_workflow_state(session_id, workflow_id) or {}
    merged = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "run_id": run_id or existing.get("run_id"),
        "trace_id": trace_id or existing.get("trace_id"),
        "current_position": current_position,
        "status": status,
        "summary": summary if summary is not None else existing.get("summary", ""),
        "pending_actions": pending_actions if pending_actions is not None else existing.get("pending_actions", []),
        "artifacts": artifacts if artifacts is not None else existing.get("artifacts", []),
        "metadata": metadata if metadata is not None else existing.get("metadata", {}),
    }
    return persist_workflow_state(merged)


def build_resume_context(session_id: str, workflow_id: str) -> dict[str, Any] | None:
    state = load_workflow_state(session_id, workflow_id)
    if not state:
        return None
    return {
        "session_id": state["session_id"],
        "workflow_id": state["workflow_id"],
        "current_position": state["current_position"],
        "status": state["status"],
        "summary": state.get("summary", ""),
        "pending_actions": state.get("pending_actions", []),
        "artifacts": state.get("artifacts", []),
        "version": state["version"],
        "updated_at": state["updated_at"],
    }


def _append_history(payload: dict[str, Any]) -> None:
    path = _history_path(str(payload["session_id"]), str(payload["workflow_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _prune_history(session_id: str, workflow_id: str) -> None:
    path = _history_path(session_id, workflow_id)
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= MAX_HISTORY:
        return
    kept = lines[-MAX_HISTORY:]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
