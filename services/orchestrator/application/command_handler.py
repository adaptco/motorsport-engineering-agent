"""Application service for deterministic execution-command handling."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from services.orchestrator.domain.models import (
    CommandType,
    ExecutionAttempt,
    ExecutionCommand,
    ExecutionLease,
    ExecutionReceipt,
    ExecutionRun,
    ExecutionState,
    new_receipt_id,
    receipt_state_hash,
    run_projection,
)
from services.orchestrator.domain.state_machine import require_transition
from services.orchestrator.ports.execution_repository import ExecutionRepository


class CommandValidationError(ValueError):
    """Normalized application error for invalid orchestrator input."""


class ExecutionCommandHandler:
    """Applies the narrow Gate 3 lifecycle without executing work externally."""

    def __init__(self, repository: ExecutionRepository) -> None:
        self._repository = repository

    def submit(self, command: ExecutionCommand) -> dict[str, Any]:
        if command.command_type is not CommandType.EXECUTION_SUBMIT:
            raise CommandValidationError("INVALID_COMMAND")
        if not command.idempotency_key or not command.workflow_type:
            raise CommandValidationError("INVALID_COMMAND")

        existing = self._repository.find_command_by_idempotency(command.idempotency_key)
        if existing:
            prior_command, run_id = existing
            if (
                prior_command.workflow_type != command.workflow_type
                or prior_command.input != command.input
                or prior_command.command_type != command.command_type
            ):
                raise CommandValidationError("IDEMPOTENCY_CONFLICT")
            return self._response_for_run(
                run_id,
                command_id=prior_command.command_id,
                idempotent_replay=True,
            )

        run = ExecutionRun.requested(command)
        self._repository.create_run(run)
        self._repository.save_command(command, run.run_id)

        event_types: list[str] = []
        run = self._append_transition(
            run,
            state=ExecutionState.REQUESTED,
            event_type="CommandAccepted",
            payload={"command_id": command.command_id, "command_type": command.command_type.value},
        )
        event_types.append("CommandAccepted")
        run = self._append_transition(
            run,
            state=ExecutionState.REQUESTED,
            event_type="ExecutionRequested",
            payload={"workflow_type": command.workflow_type, "priority": command.priority},
        )
        event_types.append("ExecutionRequested")
        require_transition(run.state, ExecutionState.SCHEDULED)
        run = self._append_transition(
            run,
            state=ExecutionState.SCHEDULED,
            event_type="ExecutionScheduled",
            payload={"workflow_type": command.workflow_type, "priority": command.priority},
        )
        event_types.append("ExecutionScheduled")

        attempt = ExecutionAttempt(
            attempt_id=f"attempt_{uuid4().hex}",
            run_id=run.run_id,
            ordinal=1,
            state=ExecutionState.ATTEMPT_CREATED,
            created_at=run.updated_at,
        )
        require_transition(run.state, ExecutionState.ATTEMPT_CREATED)
        run = self._append_transition(
            run,
            state=ExecutionState.ATTEMPT_CREATED,
            event_type="ExecutionAttemptCreated",
            payload={"attempt_id": attempt.attempt_id, "ordinal": attempt.ordinal},
            attempt_id=attempt.attempt_id,
        )
        event_types.append("ExecutionAttemptCreated")
        return self._response_for_run(
            run.run_id,
            command_id=command.command_id,
            idempotent_replay=False,
            event_types=event_types,
        )

    def acquire_lease(
        self,
        *,
        run_id: str,
        executor_id: str,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        """Record ownership for an existing attempt; no worker execution is started."""
        run = self._repository.get_run(run_id)
        if run is None:
            raise CommandValidationError("RUN_NOT_FOUND")
        if not run.current_attempt_id:
            raise CommandValidationError("ATTEMPT_NOT_FOUND")
        if self._repository.active_lease_for_run(run_id):
            raise CommandValidationError("LEASE_CONFLICT")
        require_transition(run.state, ExecutionState.LEASED)
        lease = ExecutionLease.acquire(
            run_id=run_id,
            attempt_id=run.current_attempt_id,
            executor_id=executor_id,
            ttl_seconds=ttl_seconds,
        )
        self._repository.save_lease(lease)
        run = self._append_transition(
            run,
            state=ExecutionState.LEASED,
            event_type="LeaseAcquired",
            payload={
                "lease_id": lease.lease_id,
                "attempt_id": lease.attempt_id,
                "executor_id": lease.executor_id,
                "expires_at": lease.expires_at.isoformat(),
            },
            lease_id=lease.lease_id,
        )
        response = self._response_for_run(
            run_id,
            command_id="lease_acquire",
            idempotent_replay=False,
            event_types=["LeaseAcquired"],
        )
        response["lease"] = {
            "lease_id": lease.lease_id,
            "executor_id": lease.executor_id,
            "expires_at": lease.expires_at.isoformat(),
        }
        return response

    def _append_transition(
        self,
        run: ExecutionRun,
        *,
        state: ExecutionState,
        event_type: str,
        payload: dict[str, Any],
        attempt_id: str | None = None,
        lease_id: str | None = None,
    ) -> ExecutionRun:
        now = datetime.now(UTC)
        desired = replace(
            run,
            state=state,
            aggregate_version=run.aggregate_version + 1,
            updated_at=now,
            current_attempt_id=attempt_id or run.current_attempt_id,
            current_lease_id=lease_id or run.current_lease_id,
        )
        event = self._repository.append_event(
            run_id=run.run_id,
            expected_aggregate_version=run.aggregate_version,
            event_type=event_type,
            payload=payload,
            new_run=desired,
        )
        prior_receipts = self._repository.receipts_for_run(run.run_id)
        previous_hash = prior_receipts[-1].state_hash if prior_receipts else None
        receipt = ExecutionReceipt(
            receipt_id=new_receipt_id(),
            run_id=run.run_id,
            event_id=event.event_id,
            logical_clock=len(prior_receipts) + 1,
            receipt_type=event_type,
            previous_hash=previous_hash,
            state_hash=receipt_state_hash(
                run_id=run.run_id,
                logical_clock=len(prior_receipts) + 1,
                receipt_type=event_type,
                event_id=event.event_id,
                previous_hash=previous_hash,
            ),
            created_at=event.occurred_at,
        )
        self._repository.append_receipt(receipt)
        stored = self._repository.get_run(run.run_id)
        if stored is None:
            raise RuntimeError("RUN_NOT_FOUND")
        return stored

    def _response_for_run(
        self,
        run_id: str,
        *,
        command_id: str,
        idempotent_replay: bool,
        event_types: list[str] | None = None,
    ) -> dict[str, Any]:
        run = self._repository.get_run(run_id)
        if run is None:
            raise RuntimeError("RUN_NOT_FOUND")
        events = self._repository.events_for_run(run_id)
        receipts = self._repository.receipts_for_run(run_id)
        return {
            "command_id": command_id,
            "execution_run_id": run_id,
            "status": run.state.value,
            "aggregate_version": run.aggregate_version,
            "events": event_types or [event.event_type for event in events],
            "idempotent_replay": idempotent_replay,
            "projection": run_projection(run, events=events, receipts=receipts),
        }
