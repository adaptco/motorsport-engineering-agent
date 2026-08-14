"""Execution-run lifecycle validation for the additive orchestrator kernel."""

from __future__ import annotations

from services.orchestrator.domain.models import ExecutionState


class InvalidTransitionError(ValueError):
    """Raised when a lifecycle transition is not permitted by the aggregate."""


_ALLOWED_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.REQUESTED: {ExecutionState.SCHEDULED, ExecutionState.CANCELLING},
    ExecutionState.SCHEDULED: {ExecutionState.ATTEMPT_CREATED, ExecutionState.CANCELLING},
    ExecutionState.ATTEMPT_CREATED: {ExecutionState.LEASED, ExecutionState.CANCELLING},
    ExecutionState.LEASED: {ExecutionState.RUNNING, ExecutionState.CANCELLING},
    ExecutionState.RUNNING: {
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLING,
        ExecutionState.WAITING_FOR_HITL,
    },
    ExecutionState.WAITING_FOR_HITL: {ExecutionState.RUNNING, ExecutionState.CANCELLING},
    ExecutionState.FAILED: {ExecutionState.SCHEDULED},
    ExecutionState.CANCELLING: {ExecutionState.CANCELLED},
    ExecutionState.COMPLETED: set(),
    ExecutionState.CANCELLED: set(),
}


def can_transition(current: ExecutionState, target: ExecutionState) -> bool:
    return target in _ALLOWED_TRANSITIONS[current]


def require_transition(current: ExecutionState, target: ExecutionState) -> None:
    if not can_transition(current, target):
        raise InvalidTransitionError(f"INVALID_TRANSITION: {current.value} -> {target.value}")
