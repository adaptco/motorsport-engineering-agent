"""Pydantic schemas for the narrow Gate 3 orchestration API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CorrelationInput(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)


class SubmitCommandRequest(BaseModel):
    command_type: Literal["execution.submit"]
    idempotency_key: str = Field(min_length=1, max_length=128)
    workflow_type: str = Field(min_length=1, max_length=128)
    priority: Literal["low", "normal", "high"] = "normal"
    input: dict[str, Any] = Field(default_factory=dict)
    correlation: CorrelationInput
    principal_id: str = Field(default="operator", min_length=1, max_length=128)


class LeaseRequest(BaseModel):
    executor_id: str = Field(min_length=1, max_length=128)
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


class CommandResponse(BaseModel):
    command_id: str
    execution_run_id: str
    status: str
    aggregate_version: int
    events: list[str]
    idempotent_replay: bool
    projection: dict[str, Any]
    lease: dict[str, str] | None = None


class RunListResponse(BaseModel):
    runs: list[dict[str, Any]]


class EventListResponse(BaseModel):
    events: list[dict[str, Any]]


class ReceiptListResponse(BaseModel):
    receipts: list[dict[str, Any]]
