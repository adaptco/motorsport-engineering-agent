from __future__ import annotations

from datetime import datetime, timezone

import pytest
from jsonschema import ValidationError

from shared.runtime_contracts import validate_runtime_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_event(event_type: str, lane: str, fsm_state: str) -> dict[str, object]:
    return {
        "event_type": event_type,
        "schema_version": "1.0.0",
        "event_id": "evt-1",
        "run_id": "run-1",
        "task_id": "task-1",
        "step_id": "step-1",
        "created_at": _now(),
        "lane": lane,
        "fsm_state": fsm_state,
        "prev_hash": None,
        "state_hash": "sha256:" + ("a" * 64),
        "policy_version": "policy-1",
    }


def test_valid_tool_requested_event_includes_idempotency_key() -> None:
    event = {
        **_base_event("tool.requested", "mcp", "TOOL_PENDING"),
        "payload": {
            "tool_name": "mea_ci_guardrail",
            "idempotency_key": "idem-001",
            "mode": "read",
            "arguments_digest": "sha256:" + ("b" * 64),
        },
    }
    validate_runtime_event(event)


def test_tool_requested_event_rejects_missing_idempotency_key() -> None:
    event = {
        **_base_event("tool.requested", "mcp", "TOOL_PENDING"),
        "payload": {
            "tool_name": "mea_ci_guardrail",
            "mode": "read",
            "arguments_digest": "sha256:" + ("b" * 64),
        },
    }
    with pytest.raises(ValidationError):
        validate_runtime_event(event)


def test_valid_checkpoint_persisted_event() -> None:
    event = {
        **_base_event("checkpoint.persisted", "ctx", "CHECKPOINTED"),
        "payload": {
            "checkpoint_id": "ckpt-123",
            "resume_safe": True,
            "active_step_id": "step-2",
            "completed_step_ids": ["step-1"],
            "budget": {
                "max_steps": 10,
                "steps_used": 3,
                "max_tokens_total": 40000,
                "tokens_used": 5000,
                "max_tool_calls": 8,
                "tool_calls_used": 2,
                "deadline_at": _now(),
            },
            "artifacts": [],
        },
    }
    validate_runtime_event(event)
