"""Deterministic domain objects for the additive execution kernel.

This module intentionally models only orchestration lifecycle authority. It does not
perform worker execution, invoke external tools, or replace the repository's existing
runtime-event and forensic-ledger contracts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ExecutionState(StrEnum):
    """Lifecycle states owned by the orchestrator aggregate."""

    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    ATTEMPT_CREATED = "attempt_created"
    LEASED = "leased"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    WAITING_FOR_HITL = "waiting_for_hitl"


class CommandType(StrEnum):
    """The narrow command vocabulary accepted by this gate."""

    EXECUTION_SUBMIT = "execution.submit"
    SCHEDULE = "schedule"
    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"
    CHECKPOINT = "checkpoint"


@dataclass(frozen=True)
class ExecutionCommand:
    command_id: str
    command_type: CommandType
    idempotency_key: str
    workflow_type: str
    priority: str
    input: dict[str, Any]
    request_id: str
    trace_id: str
    principal_id: str = "operator"
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ExecutionRun:
    run_id: str
    workflow_type: str
    priority: str
    state: ExecutionState
    aggregate_version: int
    trace_id: str
    request_id: str
    principal_id: str
    created_at: datetime
    updated_at: datetime
    current_attempt_id: str | None = None
    current_lease_id: str | None = None
    last_event_id: str | None = None
    last_receipt_id: str | None = None

    @classmethod
    def requested(cls, command: ExecutionCommand, *, run_id: str | None = None) -> ExecutionRun:
        now = command.issued_at
        return cls(
            run_id=run_id or f"run_{uuid4().hex}",
            workflow_type=command.workflow_type,
            priority=command.priority,
            state=ExecutionState.REQUESTED,
            aggregate_version=0,
            trace_id=command.trace_id,
            request_id=command.request_id,
            principal_id=command.principal_id,
            created_at=now,
            updated_at=now,
        )

    def evolve(
        self,
        *,
        state: ExecutionState | None = None,
        event_id: str | None = None,
        receipt_id: str | None = None,
        attempt_id: str | None = None,
        lease_id: str | None = None,
        occurred_at: datetime | None = None,
    ) -> ExecutionRun:
        return replace(
            self,
            state=state or self.state,
            aggregate_version=self.aggregate_version + 1,
            updated_at=occurred_at or datetime.now(UTC),
            last_event_id=event_id or self.last_event_id,
            last_receipt_id=receipt_id or self.last_receipt_id,
            current_attempt_id=attempt_id or self.current_attempt_id,
            current_lease_id=lease_id or self.current_lease_id,
        )


@dataclass(frozen=True)
class ExecutionAttempt:
    attempt_id: str
    run_id: str
    ordinal: int
    state: ExecutionState
    created_at: datetime


@dataclass(frozen=True)
class ExecutionLease:
    lease_id: str
    run_id: str
    attempt_id: str
    executor_id: str
    acquired_at: datetime
    expires_at: datetime

    @property
    def active(self) -> bool:
        return self.expires_at > datetime.now(UTC)

    @classmethod
    def acquire(
        cls,
        *,
        run_id: str,
        attempt_id: str,
        executor_id: str,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> ExecutionLease:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        acquired_at = now or datetime.now(UTC)
        return cls(
            lease_id=f"lease_{uuid4().hex}",
            run_id=run_id,
            attempt_id=attempt_id,
            executor_id=executor_id,
            acquired_at=acquired_at,
            expires_at=acquired_at + timedelta(seconds=ttl_seconds),
        )


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    event_type: str
    run_id: str
    aggregate_version: int
    global_event_index: int
    occurred_at: datetime
    payload: dict[str, Any]
    payload_hash: str
    previous_global_hash: str | None
    global_hash: str


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    run_id: str
    event_id: str
    logical_clock: int
    receipt_type: str
    previous_hash: str | None
    state_hash: str
    created_at: datetime


def canonical_json(value: Any) -> str:
    """Serialize domain evidence canonically, compatible with the forensic ledger."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_prefixed(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()}"


def event_payload_hash(payload: dict[str, Any]) -> str:
    return sha256_prefixed(payload)


def event_global_hash(
    *,
    event_id: str,
    event_type: str,
    run_id: str,
    aggregate_version: int,
    global_event_index: int,
    occurred_at: datetime,
    payload_hash: str,
    previous_global_hash: str | None,
) -> str:
    return sha256_prefixed(
        {
            "event_id": event_id,
            "event_type": event_type,
            "run_id": run_id,
            "aggregate_version": aggregate_version,
            "global_event_index": global_event_index,
            "occurred_at": occurred_at.isoformat(),
            "payload_hash": payload_hash,
            "previous_global_hash": previous_global_hash,
        }
    )


def receipt_state_hash(
    *,
    run_id: str,
    logical_clock: int,
    receipt_type: str,
    event_id: str,
    previous_hash: str | None,
) -> str:
    return sha256_prefixed(
        {
            "run_id": run_id,
            "logical_clock": logical_clock,
            "receipt_type": receipt_type,
            "event_id": event_id,
            "previous_hash": previous_hash,
        }
    )


def new_command_id() -> str:
    return f"cmd_{uuid4().hex}"


def new_event_id() -> str:
    return f"evt_{uuid4().hex}"


def new_receipt_id() -> str:
    return f"rcpt_{uuid4().hex}"


def serialize_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def event_as_dict(event: RuntimeEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "aggregate_type": "execution_run",
        "aggregate_id": event.run_id,
        "aggregate_version": event.aggregate_version,
        "global_event_index": event.global_event_index,
        "occurred_at": serialize_datetime(event.occurred_at),
        "payload": event.payload,
        "payload_hash": event.payload_hash,
        "previous_global_hash": event.previous_global_hash,
        "global_hash": event.global_hash,
    }


def receipt_as_dict(receipt: ExecutionReceipt) -> dict[str, Any]:
    return {
        "receipt_id": receipt.receipt_id,
        "run_id": receipt.run_id,
        "event_id": receipt.event_id,
        "logical_clock": receipt.logical_clock,
        "receipt_type": receipt.receipt_type,
        "previous_hash": receipt.previous_hash,
        "state_hash": receipt.state_hash,
        "created_at": serialize_datetime(receipt.created_at),
    }


def run_projection(
    run: ExecutionRun, *, events: list[RuntimeEvent], receipts: list[ExecutionReceipt]
) -> dict[str, Any]:
    """Build a stable read projection without mutating the aggregate."""

    return {
        "run_id": run.run_id,
        "workflow_type": run.workflow_type,
        "priority": run.priority,
        "status": run.state.value,
        "aggregate_version": run.aggregate_version,
        "trace_id": run.trace_id,
        "request_id": run.request_id,
        "principal_id": run.principal_id,
        "current_attempt_id": run.current_attempt_id,
        "current_lease_id": run.current_lease_id,
        "last_event": event_as_dict(events[-1]) if events else None,
        "last_receipt": receipt_as_dict(receipts[-1]) if receipts else None,
        "event_count": len(events),
        "receipt_count": len(receipts),
        "created_at": serialize_datetime(run.created_at),
        "updated_at": serialize_datetime(run.updated_at),
    }
