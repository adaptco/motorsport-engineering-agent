"""Additive control-plane routes for the deterministic execution kernel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from services.orchestrator.api.schemas import (
    CommandResponse,
    EventListResponse,
    LeaseRequest,
    ReceiptListResponse,
    RunListResponse,
    SubmitCommandRequest,
)
from services.orchestrator.application.command_handler import (
    CommandValidationError,
    ExecutionCommandHandler,
)
from services.orchestrator.domain.models import (
    CommandType,
    ExecutionCommand,
    event_as_dict,
    new_command_id,
    receipt_as_dict,
    run_projection,
)
from services.orchestrator.infrastructure.in_memory_execution_repository import (
    InMemoryExecutionRepository,
)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])
_repository = InMemoryExecutionRepository()
_handler = ExecutionCommandHandler(_repository)


def reset_orchestrator_runtime() -> None:
    """Reset the transitional in-memory adapter for isolated test lifecycles."""

    global _repository, _handler
    _repository = InMemoryExecutionRepository()
    _handler = ExecutionCommandHandler(_repository)


def _error(code: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code})


def _translate_error(exc: Exception) -> HTTPException:
    code = str(exc).split(":", maxsplit=1)[0]
    if code in {"RUN_NOT_FOUND", "ATTEMPT_NOT_FOUND"}:
        return _error(code, 404)
    if code in {"LEASE_CONFLICT", "IDEMPOTENCY_CONFLICT", "STALE_AGGREGATE_VERSION"}:
        return _error(code, 409)
    if code in {"INVALID_COMMAND", "INVALID_TRANSITION"}:
        return _error(code, 422)
    return _error("RECEIPT_INTEGRITY_FAILURE", 500)


@router.post("/commands", response_model=CommandResponse, status_code=201)
def submit_command(payload: SubmitCommandRequest) -> dict[str, Any]:
    command = ExecutionCommand(
        command_id=new_command_id(),
        command_type=CommandType(payload.command_type),
        idempotency_key=payload.idempotency_key,
        workflow_type=payload.workflow_type,
        priority=payload.priority,
        input=payload.input,
        request_id=payload.correlation.request_id,
        trace_id=payload.correlation.trace_id,
        principal_id=payload.principal_id,
    )
    try:
        result = _handler.submit(command)
    except (CommandValidationError, ValueError, KeyError) as exc:
        raise _translate_error(exc) from exc
    return result


@router.post("/runs/{run_id}/leases", response_model=CommandResponse)
def acquire_lease(run_id: str, payload: LeaseRequest) -> dict[str, Any]:
    try:
        return _handler.acquire_lease(
            run_id=run_id,
            executor_id=payload.executor_id,
            ttl_seconds=payload.ttl_seconds,
        )
    except (CommandValidationError, ValueError, KeyError) as exc:
        raise _translate_error(exc) from exc


@router.get("/runs", response_model=RunListResponse)
def list_runs(
    status: str | None = Query(default=None, max_length=64),
) -> dict[str, list[dict[str, Any]]]:
    runs = _repository.list_runs(status=status)
    return {
        "runs": [
            run_projection(
                run,
                events=_repository.events_for_run(run.run_id),
                receipts=_repository.receipts_for_run(run.run_id),
            )
            for run in runs
        ]
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    run = _repository.get_run(run_id)
    if run is None:
        raise _error("RUN_NOT_FOUND", 404)
    return run_projection(
        run,
        events=_repository.events_for_run(run_id),
        receipts=_repository.receipts_for_run(run_id),
    )


@router.get("/runs/{run_id}/events", response_model=EventListResponse)
def get_events(run_id: str) -> dict[str, list[dict[str, Any]]]:
    try:
        return {"events": [event_as_dict(event) for event in _repository.events_for_run(run_id)]}
    except KeyError as exc:
        raise _error("RUN_NOT_FOUND", 404) from exc


@router.get("/runs/{run_id}/receipts", response_model=ReceiptListResponse)
def get_receipts(run_id: str) -> dict[str, list[dict[str, Any]]]:
    try:
        return {
            "receipts": [
                receipt_as_dict(receipt) for receipt in _repository.receipts_for_run(run_id)
            ]
        }
    except KeyError as exc:
        raise _error("RUN_NOT_FOUND", 404) from exc


@router.get("/runs/{run_id}/projection")
def get_projection(run_id: str) -> dict[str, Any]:
    return get_run(run_id)
