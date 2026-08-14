"""Validation tests for additive execution-control contracts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "runtime" / "execution-control.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _now() -> str:
    return datetime.now(UTC).isoformat()


def test_execution_command_contract_accepts_bounded_resume_command() -> None:
    command = {
        "command_id": str(uuid4()),
        "command_type": "RESUME",
        "run_id": "run-42",
        "payload": {"checkpoint_id": "checkpoint-7"},
        "issued_at": _now(),
        "principal_id": "operator-1",
        "authz_scope": "runtime:resume",
        "idempotency_key": "resume-run-42-checkpoint-7",
    }

    _validator().validate(command)


def test_execution_lease_contract_accepts_active_worker_lease() -> None:
    lease = {
        "lease_id": str(uuid4()),
        "run_id": "run-42",
        "agent_id": "worker-a",
        "acquired_at": _now(),
        "ttl_seconds": 300,
        "status": "active",
        "capabilities": ["read:telemetry", "invoke:mcp"],
    }

    _validator().validate(lease)


def test_execution_control_contract_rejects_invalid_command() -> None:
    invalid_command = {
        "command_type": "DELETE",
        "run_id": "run-42",
        "payload": {},
        "issued_at": _now(),
    }

    with pytest.raises(ValidationError):
        _validator().validate(invalid_command)
