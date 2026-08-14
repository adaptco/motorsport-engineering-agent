"""Thread-safe in-memory adapter for the Gate 3 execution repository port."""

from __future__ import annotations

from threading import RLock
from typing import Any

from services.orchestrator.domain.models import (
    ExecutionCommand,
    ExecutionLease,
    ExecutionReceipt,
    ExecutionRun,
    RuntimeEvent,
    event_global_hash,
    event_payload_hash,
    new_event_id,
)
from services.orchestrator.ports.execution_repository import ExecutionRepository


class StaleAggregateVersionError(ValueError):
    """Raised when an append does not match the aggregate's current version."""


class InMemoryExecutionRepository(ExecutionRepository):
    """A deterministic adapter intended for test and transitional runtime use only."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._commands: dict[str, tuple[ExecutionCommand, str]] = {}
        self._runs: dict[str, ExecutionRun] = {}
        self._events: dict[str, list[RuntimeEvent]] = {}
        self._receipts: dict[str, list[ExecutionReceipt]] = {}
        self._leases: dict[str, ExecutionLease] = {}
        self._global_event_index = 0
        self._previous_global_hash: str | None = None

    def find_command_by_idempotency(
        self, idempotency_key: str
    ) -> tuple[ExecutionCommand, str] | None:
        with self._lock:
            return self._commands.get(idempotency_key)

    def save_command(self, command: ExecutionCommand, run_id: str) -> None:
        with self._lock:
            existing = self._commands.get(command.idempotency_key)
            if existing and existing[0].command_id != command.command_id:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            self._commands[command.idempotency_key] = (command, run_id)

    def create_run(self, run: ExecutionRun) -> None:
        with self._lock:
            if run.run_id in self._runs:
                raise ValueError("RUN_ALREADY_EXISTS")
            self._runs[run.run_id] = run
            self._events[run.run_id] = []
            self._receipts[run.run_id] = []

    def get_run(self, run_id: str) -> ExecutionRun | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self, *, status: str | None = None) -> list[ExecutionRun]:
        with self._lock:
            runs = list(self._runs.values())
        if status:
            runs = [run for run in runs if run.state.value == status]
        return sorted(runs, key=lambda run: (run.created_at, run.run_id))

    def active_lease_for_run(self, run_id: str) -> ExecutionLease | None:
        with self._lock:
            lease = self._leases.get(run_id)
            return lease if lease and lease.active else None

    def save_lease(self, lease: ExecutionLease) -> None:
        with self._lock:
            if lease.run_id not in self._runs:
                raise KeyError("RUN_NOT_FOUND")
            active = self.active_lease_for_run(lease.run_id)
            if active and active.lease_id != lease.lease_id:
                raise ValueError("LEASE_CONFLICT")
            self._leases[lease.run_id] = lease

    def append_event(
        self,
        *,
        run_id: str,
        expected_aggregate_version: int,
        event_type: str,
        payload: dict[str, Any],
        new_run: ExecutionRun,
    ) -> RuntimeEvent:
        with self._lock:
            current = self._runs.get(run_id)
            if current is None:
                raise KeyError("RUN_NOT_FOUND")
            if current.aggregate_version != expected_aggregate_version:
                raise StaleAggregateVersionError(
                    f"STALE_AGGREGATE_VERSION: expected={expected_aggregate_version}, actual={current.aggregate_version}"
                )
            if new_run.aggregate_version != current.aggregate_version + 1:
                raise ValueError("INVALID_AGGREGATE_VERSION")
            self._global_event_index += 1
            payload_hash = event_payload_hash(payload)
            event_id = new_event_id()
            event = RuntimeEvent(
                event_id=event_id,
                event_type=event_type,
                run_id=run_id,
                aggregate_version=new_run.aggregate_version,
                global_event_index=self._global_event_index,
                occurred_at=new_run.updated_at,
                payload=dict(payload),
                payload_hash=payload_hash,
                previous_global_hash=self._previous_global_hash,
                global_hash=event_global_hash(
                    event_id=event_id,
                    event_type=event_type,
                    run_id=run_id,
                    aggregate_version=new_run.aggregate_version,
                    global_event_index=self._global_event_index,
                    occurred_at=new_run.updated_at,
                    payload_hash=payload_hash,
                    previous_global_hash=self._previous_global_hash,
                ),
            )
            self._events[run_id].append(event)
            self._runs[run_id] = new_run.evolve(
                state=new_run.state,
                event_id=event.event_id,
                occurred_at=new_run.updated_at,
            )
            # Evolve increments aggregate_version, so retain the event's version exactly.
            self._runs[run_id] = ExecutionRun(
                **{**self._runs[run_id].__dict__, "aggregate_version": new_run.aggregate_version}
            )
            self._previous_global_hash = event.global_hash
            return event

    def append_receipt(self, receipt: ExecutionReceipt) -> None:
        with self._lock:
            if receipt.run_id not in self._runs:
                raise KeyError("RUN_NOT_FOUND")
            existing = self._receipts[receipt.run_id]
            if existing and receipt.logical_clock != existing[-1].logical_clock + 1:
                raise ValueError("RECEIPT_INTEGRITY_FAILURE")
            if not existing and receipt.logical_clock != 1:
                raise ValueError("RECEIPT_INTEGRITY_FAILURE")
            self._receipts[receipt.run_id].append(receipt)
            run = self._runs[receipt.run_id]
            self._runs[receipt.run_id] = ExecutionRun(
                **{**run.__dict__, "last_receipt_id": receipt.receipt_id}
            )

    def events_for_run(self, run_id: str) -> list[RuntimeEvent]:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError("RUN_NOT_FOUND")
            return list(self._events[run_id])

    def receipts_for_run(self, run_id: str) -> list[ExecutionReceipt]:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError("RUN_NOT_FOUND")
            return list(self._receipts[run_id])
