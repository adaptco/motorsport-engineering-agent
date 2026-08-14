from __future__ import annotations

import asyncio
from collections import deque
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from services.orchestrator.domain.models import (
    CommandType,
    ExecutionCommand,
    ExecutionLease,
    ExecutionReceipt,
    ExecutionRun,
    ExecutionState,
    event_global_hash,
    receipt_state_hash,
)
from services.orchestrator.infrastructure.in_memory_execution_repository import (
    StaleAggregateVersionError,
)
from services.orchestrator.infrastructure.postgres_execution_repository import (
    PostgresExecutionRepository,
)

NOW = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


class _AsyncContext(AbstractAsyncContextManager[Any]):
    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None


class ScriptedCursor(_AsyncContext):
    def __init__(
        self,
        *,
        one: list[dict[str, Any] | None] | None = None,
        many: list[list[dict[str, Any]]] | None = None,
    ) -> None:
        self.one = deque(one or [])
        self.many = deque(many or [])
        self.statements: list[tuple[str, tuple[Any, ...] | None]] = []

    async def execute(self, statement: str, params: tuple[Any, ...] | None = None) -> None:
        self.statements.append((statement, params))

    async def fetchone(self) -> dict[str, Any] | None:
        return self.one.popleft() if self.one else None

    async def fetchall(self) -> list[dict[str, Any]]:
        return self.many.popleft() if self.many else []


class ScriptedConnection(_AsyncContext):
    def __init__(self, cursor: ScriptedCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> ScriptedCursor:
        return self._cursor

    def transaction(self) -> _AsyncContext:
        return _AsyncContext()


def command(*, command_id: str = "cmd-test") -> ExecutionCommand:
    return ExecutionCommand(
        command_id=command_id,
        command_type=CommandType.EXECUTION_SUBMIT,
        idempotency_key="key-test",
        workflow_type="aero.analysis",
        priority="normal",
        input={"lap": 12},
        request_id="request-test",
        trace_id="trace-test",
        principal_id="operator-test",
        issued_at=NOW,
    )


def run(*, version: int = 0, state: ExecutionState = ExecutionState.REQUESTED) -> ExecutionRun:
    return ExecutionRun(
        run_id="run-test",
        workflow_type="aero.analysis",
        priority="normal",
        state=state,
        aggregate_version=version,
        trace_id="trace-test",
        request_id="request-test",
        principal_id="operator-test",
        created_at=NOW,
        updated_at=NOW + timedelta(seconds=version),
        current_attempt_id="attempt-test" if version else None,
        current_lease_id="lease-test" if version > 1 else None,
        last_event_id="evt-prior" if version else None,
        last_receipt_id="rcpt-prior" if version else None,
    )


def run_row(value: ExecutionRun) -> dict[str, Any]:
    return {
        "run_id": value.run_id,
        "workflow_type": value.workflow_type,
        "priority": value.priority,
        "state": value.state.value,
        "aggregate_version": value.aggregate_version,
        "trace_id": value.trace_id,
        "request_id": value.request_id,
        "principal_id": value.principal_id,
        "current_attempt_id": value.current_attempt_id,
        "current_lease_id": value.current_lease_id,
        "last_event_id": value.last_event_id,
        "last_receipt_id": value.last_receipt_id,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def repository(
    *,
    one: list[dict[str, Any] | None] | None = None,
    many: list[list[dict[str, Any]]] | None = None,
) -> tuple[PostgresExecutionRepository, ScriptedCursor]:
    cursor = ScriptedCursor(one=one, many=many)
    connection = ScriptedConnection(cursor)

    async def factory() -> ScriptedConnection:
        return connection

    return PostgresExecutionRepository(connection_factory=factory), cursor


def run_async(awaitable: Any) -> Any:
    return asyncio.run(awaitable)


def test_find_command_and_create_run_rehydrate_existing_contract() -> None:
    existing = command()
    repo, cursor = repository(
        one=[
            {
                "command_id": existing.command_id,
                "command_type": existing.command_type.value,
                "idempotency_key": existing.idempotency_key,
                "workflow_type": existing.workflow_type,
                "priority": existing.priority,
                "input": existing.input,
                "request_id": existing.request_id,
                "trace_id": existing.trace_id,
                "principal_id": existing.principal_id,
                "issued_at": existing.issued_at,
                "run_id": "run-test",
            }
        ]
    )

    found = run_async(repo.find_command_by_idempotency("key-test"))

    assert found == (existing, "run-test")
    assert "FROM orchestrator_commands" in cursor.statements[0][0]

    repo, cursor = repository(one=[{"run_id": "run-test"}])
    run_async(repo.create_run(run()))
    assert cursor.statements[0][1] == PostgresExecutionRepository._run_values(run())


def test_command_persistence_handles_first_write_and_conflict() -> None:
    repo, _ = repository(one=[{"command_id": "cmd-test"}])
    run_async(repo.save_command(command(), "run-test"))

    repo, _ = repository(one=[None, {"command_id": "cmd-other"}])
    with pytest.raises(ValueError, match="IDEMPOTENCY_CONFLICT"):
        run_async(repo.save_command(command(), "run-test"))


def test_run_read_models_support_get_and_filtered_or_unfiltered_lists() -> None:
    requested = run()
    scheduled = run(version=1, state=ExecutionState.SCHEDULED)

    repo, _ = repository(one=[run_row(requested)])
    assert run_async(repo.get_run("run-test")) == requested

    repo, filtered_cursor = repository(many=[[run_row(scheduled)]])
    assert run_async(repo.list_runs(status="scheduled")) == [scheduled]
    assert "WHERE state" in filtered_cursor.statements[0][0]

    repo, all_cursor = repository(many=[[run_row(requested), run_row(scheduled)]])
    assert run_async(repo.list_runs()) == [requested, scheduled]
    assert "WHERE state" not in all_cursor.statements[0][0]


def test_leases_are_rehydrated_and_persisted_with_safety_checks() -> None:
    lease = ExecutionLease(
        lease_id="lease-test",
        run_id="run-test",
        attempt_id="attempt-test",
        executor_id="executor-test",
        acquired_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    lease_row = {
        "lease_id": lease.lease_id,
        "run_id": lease.run_id,
        "attempt_id": lease.attempt_id,
        "executor_id": lease.executor_id,
        "acquired_at": lease.acquired_at,
        "expires_at": lease.expires_at,
    }

    repo, _ = repository(one=[lease_row])
    assert run_async(repo.active_lease_for_run("run-test")) == lease

    repo, _ = repository(one=[{"run_id": "run-test"}, None])
    run_async(repo.save_lease(lease))

    repo, _ = repository(one=[None])
    with pytest.raises(KeyError, match="RUN_NOT_FOUND"):
        run_async(repo.save_lease(lease))

    repo, _ = repository(one=[{"run_id": "run-test"}, {"lease_id": "lease-other"}])
    with pytest.raises(ValueError, match="LEASE_CONFLICT"):
        run_async(repo.save_lease(lease))


def test_append_event_preserves_optimistic_concurrency_and_global_hash_chain() -> None:
    current = run()
    desired = run(version=1, state=ExecutionState.SCHEDULED)
    previous_hash = "sha256:previous"
    repo, cursor = repository(
        one=[run_row(current), {"global_hash": previous_hash}, {"global_event_index": 7}]
    )

    event = run_async(
        repo.append_event(
            run_id=current.run_id,
            expected_aggregate_version=0,
            event_type="ExecutionScheduled",
            payload={"workflow_type": "aero.analysis"},
            new_run=desired,
        )
    )

    assert event.aggregate_version == 1
    assert event.global_event_index == 7
    assert event.previous_global_hash == previous_hash
    assert event.global_hash == event_global_hash(
        event_id=event.event_id,
        event_type=event.event_type,
        run_id=event.run_id,
        aggregate_version=event.aggregate_version,
        global_event_index=event.global_event_index,
        occurred_at=event.occurred_at,
        payload_hash=event.payload_hash,
        previous_global_hash=previous_hash,
    )
    assert any("pg_advisory_xact_lock" in statement for statement, _ in cursor.statements)

    repo, _ = repository(one=[None])
    with pytest.raises(KeyError, match="RUN_NOT_FOUND"):
        run_async(
            repo.append_event(
                run_id=current.run_id,
                expected_aggregate_version=0,
                event_type="ExecutionScheduled",
                payload={},
                new_run=desired,
            )
        )

    repo, _ = repository(one=[run_row(run(version=2))])
    with pytest.raises(StaleAggregateVersionError, match="STALE_AGGREGATE_VERSION"):
        run_async(
            repo.append_event(
                run_id=current.run_id,
                expected_aggregate_version=0,
                event_type="ExecutionScheduled",
                payload={},
                new_run=desired,
            )
        )

    repo, _ = repository(one=[run_row(current)])
    with pytest.raises(ValueError, match="INVALID_AGGREGATE_VERSION"):
        run_async(
            repo.append_event(
                run_id=current.run_id,
                expected_aggregate_version=0,
                event_type="ExecutionScheduled",
                payload={},
                new_run=run(version=2),
            )
        )


def test_append_receipt_enforces_contiguous_logical_chain() -> None:
    receipt = ExecutionReceipt(
        receipt_id="rcpt-test",
        run_id="run-test",
        event_id="evt-test",
        logical_clock=1,
        receipt_type="ExecutionScheduled",
        previous_hash=None,
        state_hash=receipt_state_hash(
            run_id="run-test",
            logical_clock=1,
            receipt_type="ExecutionScheduled",
            event_id="evt-test",
            previous_hash=None,
        ),
        created_at=NOW,
    )
    repo, _ = repository(one=[{"run_id": "run-test"}, None])
    run_async(repo.append_receipt(receipt))

    repo, _ = repository(one=[{"run_id": "run-test"}, {"logical_clock": 1, "state_hash": "old"}])
    with pytest.raises(ValueError, match="RECEIPT_INTEGRITY_FAILURE"):
        run_async(repo.append_receipt(receipt))

    repo, _ = repository(one=[None])
    with pytest.raises(KeyError, match="RUN_NOT_FOUND"):
        run_async(repo.append_receipt(receipt))


def test_event_and_receipt_read_models_preserve_ordered_evidence() -> None:
    event_row = {
        "event_id": "evt-test",
        "event_type": "ExecutionScheduled",
        "run_id": "run-test",
        "aggregate_version": 1,
        "global_event_index": 2,
        "occurred_at": NOW,
        "payload": {"scheduled": True},
        "payload_hash": "sha256:payload",
        "previous_global_hash": None,
        "global_hash": "sha256:event",
    }
    receipt_row = {
        "receipt_id": "rcpt-test",
        "run_id": "run-test",
        "event_id": "evt-test",
        "logical_clock": 1,
        "receipt_type": "ExecutionScheduled",
        "previous_hash": None,
        "state_hash": "sha256:receipt",
        "created_at": NOW,
    }

    repo, _ = repository(one=[{"run_id": "run-test"}], many=[[event_row]])
    events = run_async(repo.events_for_run("run-test"))
    assert [event.event_id for event in events] == ["evt-test"]

    repo, _ = repository(one=[{"run_id": "run-test"}], many=[[receipt_row]])
    receipts = run_async(repo.receipts_for_run("run-test"))
    assert [receipt.receipt_id for receipt in receipts] == ["rcpt-test"]

    repo, _ = repository(one=[None])
    with pytest.raises(KeyError, match="RUN_NOT_FOUND"):
        run_async(repo.events_for_run("run-test"))
    repo, _ = repository(one=[None])
    with pytest.raises(KeyError, match="RUN_NOT_FOUND"):
        run_async(repo.receipts_for_run("run-test"))


def test_execution_store_migration_is_additive_and_contains_required_guards() -> None:
    migration = Path("db/migrations/005_orchestrator_execution_store.sql").read_text()

    assert "CREATE TABLE IF NOT EXISTS orchestrator_runs" in migration
    assert "CREATE TABLE IF NOT EXISTS orchestrator_commands" in migration
    assert "CREATE TABLE IF NOT EXISTS orchestrator_leases" in migration
    assert "CREATE TABLE IF NOT EXISTS orchestrator_events" in migration
    assert "CREATE TABLE IF NOT EXISTS orchestrator_receipts" in migration
    assert "UNIQUE (run_id, aggregate_version)" in migration
    assert "UNIQUE (run_id, logical_clock)" in migration
    assert "ON DELETE RESTRICT" in migration
    assert "-- DOWN (manual" in migration


def test_adapter_configuration_and_invalid_database_datetime_are_explicit() -> None:
    repo, _ = repository()
    assert repo._database_url.startswith("postgresql://")
    with pytest.raises(TypeError, match="DATABASE_DATETIME_INVALID"):
        PostgresExecutionRepository._utc("not-a-timestamp")
