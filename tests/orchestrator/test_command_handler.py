from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from services.orchestrator.application.command_handler import (
    CommandValidationError,
    ExecutionCommandHandler,
)
from services.orchestrator.domain.models import (
    CommandType,
    ExecutionCommand,
    ExecutionRun,
    ExecutionState,
    event_global_hash,
    receipt_state_hash,
)
from services.orchestrator.infrastructure.in_memory_execution_repository import (
    InMemoryExecutionRepository,
    StaleAggregateVersionError,
)


def command(*, key: str = "key-1", workflow: str = "repo.fix_ci") -> ExecutionCommand:
    return ExecutionCommand(
        command_id="cmd-test",
        command_type=CommandType.EXECUTION_SUBMIT,
        idempotency_key=key,
        workflow_type=workflow,
        priority="normal",
        input={"repository": "adaptco/motorsport-engineering-agent", "target": "example"},
        request_id="req-test",
        trace_id="trace-test",
        issued_at=datetime(2026, 8, 14, tzinfo=UTC),
    )


def test_submit_command_emits_deterministic_lifecycle_and_projection() -> None:
    repository = InMemoryExecutionRepository()
    handler = ExecutionCommandHandler(repository)

    result = handler.submit(command())

    assert result["status"] == "attempt_created"
    assert result["events"] == [
        "CommandAccepted",
        "ExecutionRequested",
        "ExecutionScheduled",
        "ExecutionAttemptCreated",
    ]
    assert result["aggregate_version"] == 4
    assert result["projection"]["event_count"] == 4
    assert result["projection"]["receipt_count"] == 4
    events = repository.events_for_run(result["execution_run_id"])
    receipts = repository.receipts_for_run(result["execution_run_id"])
    assert [event.aggregate_version for event in events] == [1, 2, 3, 4]
    assert [event.global_event_index for event in events] == [1, 2, 3, 4]
    assert [receipt.logical_clock for receipt in receipts] == [1, 2, 3, 4]
    assert all(
        event.global_hash
        == event_global_hash(
            event_id=event.event_id,
            event_type=event.event_type,
            run_id=event.run_id,
            aggregate_version=event.aggregate_version,
            global_event_index=event.global_event_index,
            occurred_at=event.occurred_at,
            payload_hash=event.payload_hash,
            previous_global_hash=event.previous_global_hash,
        )
        for event in events
    )
    assert all(
        receipt.state_hash
        == receipt_state_hash(
            run_id=receipt.run_id,
            logical_clock=receipt.logical_clock,
            receipt_type=receipt.receipt_type,
            event_id=receipt.event_id,
            previous_hash=receipt.previous_hash,
        )
        for receipt in receipts
    )


def test_submit_command_replays_same_idempotency_key_without_new_events() -> None:
    repository = InMemoryExecutionRepository()
    handler = ExecutionCommandHandler(repository)

    first = handler.submit(command())
    replay = handler.submit(command())

    assert replay["idempotent_replay"] is True
    assert replay["execution_run_id"] == first["execution_run_id"]
    assert len(repository.events_for_run(first["execution_run_id"])) == 4


def test_submit_command_rejects_idempotency_payload_conflict() -> None:
    repository = InMemoryExecutionRepository()
    handler = ExecutionCommandHandler(repository)
    handler.submit(command())

    with pytest.raises(CommandValidationError, match="IDEMPOTENCY_CONFLICT"):
        handler.submit(command(workflow="repo.different"))


def test_lease_acquisition_is_recorded_and_conflicting_lease_is_rejected() -> None:
    repository = InMemoryExecutionRepository()
    handler = ExecutionCommandHandler(repository)
    run_id = handler.submit(command())["execution_run_id"]

    lease = handler.acquire_lease(run_id=run_id, executor_id="agent-test", ttl_seconds=60)

    assert lease["status"] == "leased"
    assert lease["lease"]["executor_id"] == "agent-test"
    with pytest.raises(CommandValidationError, match="LEASE_CONFLICT"):
        handler.acquire_lease(run_id=run_id, executor_id="agent-other", ttl_seconds=60)


def test_repository_rejects_stale_expected_aggregate_version() -> None:
    repository = InMemoryExecutionRepository()
    run = ExecutionRun.requested(command())
    repository.create_run(run)
    changed = replace(run, aggregate_version=1, updated_at=datetime.now(UTC))
    repository.append_event(
        run_id=run.run_id,
        expected_aggregate_version=0,
        event_type="CommandAccepted",
        payload={},
        new_run=changed,
    )

    with pytest.raises(StaleAggregateVersionError, match="STALE_AGGREGATE_VERSION"):
        repository.append_event(
            run_id=run.run_id,
            expected_aggregate_version=0,
            event_type="ExecutionRequested",
            payload={},
            new_run=replace(changed, aggregate_version=2, state=ExecutionState.REQUESTED),
        )
