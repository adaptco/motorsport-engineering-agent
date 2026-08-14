"""Port for deterministic execution-run persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.orchestrator.domain.models import (
    ExecutionCommand,
    ExecutionLease,
    ExecutionReceipt,
    ExecutionRun,
    RuntimeEvent,
)


class ExecutionRepository(ABC):
    """Persistence boundary shared by the application service and future adapters."""

    @abstractmethod
    def find_command_by_idempotency(
        self, idempotency_key: str
    ) -> tuple[ExecutionCommand, str] | None:
        """Return the original command and run identifier for an idempotent replay."""

    @abstractmethod
    def save_command(self, command: ExecutionCommand, run_id: str) -> None:
        """Persist a command idempotency mapping."""

    @abstractmethod
    def create_run(self, run: ExecutionRun) -> None:
        """Create an aggregate at version zero."""

    @abstractmethod
    def get_run(self, run_id: str) -> ExecutionRun | None:
        """Fetch the aggregate read model."""

    @abstractmethod
    def list_runs(self, *, status: str | None = None) -> list[ExecutionRun]:
        """List run aggregates, optionally by lifecycle state."""

    @abstractmethod
    def active_lease_for_run(self, run_id: str) -> ExecutionLease | None:
        """Return an active lease for the aggregate, if any."""

    @abstractmethod
    def save_lease(self, lease: ExecutionLease) -> None:
        """Persist a time-bounded immutable execution lease."""

    @abstractmethod
    def append_event(
        self,
        *,
        run_id: str,
        expected_aggregate_version: int,
        event_type: str,
        payload: dict[str, Any],
        new_run: ExecutionRun,
    ) -> RuntimeEvent:
        """Append one aggregate event with optimistic-concurrency enforcement."""

    @abstractmethod
    def append_receipt(self, receipt: ExecutionReceipt) -> None:
        """Persist one immutable receipt after its source event has appended."""

    @abstractmethod
    def events_for_run(self, run_id: str) -> list[RuntimeEvent]:
        """Return events ordered by aggregate version."""

    @abstractmethod
    def receipts_for_run(self, run_id: str) -> list[ExecutionReceipt]:
        """Return receipts ordered by logical clock."""
