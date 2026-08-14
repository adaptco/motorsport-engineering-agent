"""Asynchronous persistence port for durable execution-run adapters."""

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


class AsyncExecutionRepository(ABC):
    """Async persistence boundary for a future async command handler.

    This port intentionally parallels :class:`ExecutionRepository` rather than
    modifying the existing synchronous application service. The current Gate 3
    API continues to use its explicit in-memory transitional adapter until an
    async application-service integration is approved.
    """

    @abstractmethod
    async def find_command_by_idempotency(
        self, idempotency_key: str
    ) -> tuple[ExecutionCommand, str] | None:
        """Return the original command and run identifier for idempotent replay."""

    @abstractmethod
    async def save_command(self, command: ExecutionCommand, run_id: str) -> None:
        """Persist a command idempotency mapping."""

    @abstractmethod
    async def create_run(self, run: ExecutionRun) -> None:
        """Create an aggregate at version zero."""

    @abstractmethod
    async def get_run(self, run_id: str) -> ExecutionRun | None:
        """Fetch the aggregate read model."""

    @abstractmethod
    async def list_runs(self, *, status: str | None = None) -> list[ExecutionRun]:
        """List run aggregates, optionally by lifecycle state."""

    @abstractmethod
    async def active_lease_for_run(self, run_id: str) -> ExecutionLease | None:
        """Return the active lease for an aggregate, if any."""

    @abstractmethod
    async def save_lease(self, lease: ExecutionLease) -> None:
        """Persist a time-bounded immutable execution lease."""

    @abstractmethod
    async def append_event(
        self,
        *,
        run_id: str,
        expected_aggregate_version: int,
        event_type: str,
        payload: dict[str, Any],
        new_run: ExecutionRun,
    ) -> RuntimeEvent:
        """Append an event with optimistic-concurrency enforcement."""

    @abstractmethod
    async def append_receipt(self, receipt: ExecutionReceipt) -> None:
        """Persist an immutable receipt after its source event appends."""

    @abstractmethod
    async def events_for_run(self, run_id: str) -> list[RuntimeEvent]:
        """Return events ordered by aggregate version."""

    @abstractmethod
    async def receipts_for_run(self, run_id: str) -> list[ExecutionReceipt]:
        """Return receipts ordered by logical clock."""
