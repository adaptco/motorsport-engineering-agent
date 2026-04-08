from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator


AGENT_IDS = Literal["planner", "researcher", "coder", "reviewer", "tester"]


class MCPEnvelope(BaseModel):
    protocol: str = "ANP"
    lease_seconds: int = Field(default=900, ge=1)
    checkpoint_required: bool = True
    handoff_required: bool = True


class MCPAgentContract(BaseModel):
    agent_id: AGENT_IDS
    name: str
    role: AGENT_IDS
    concurrency_limit: int = Field(default=1, ge=1)
    capabilities: list[str] = Field(default_factory=list)
    tool_scopes: list[str] = Field(default_factory=list)
    resource_uris: list[str] = Field(default_factory=list)
    envelope: MCPEnvelope = Field(default_factory=MCPEnvelope)

    @field_validator("capabilities", "tool_scopes", "resource_uris")
    @classmethod
    def _normalize_unique_strings(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("list entries must be unique")
        return cleaned

    @model_validator(mode="after")
    def _validate_agent_alignment(self) -> "MCPAgentContract":
        if self.agent_id != self.role:
            raise ValueError("agent_id and role must match")
        if not self.capabilities:
            raise ValueError("capabilities must not be empty")
        return self


class MCPRuntimeConfig(BaseModel):
    runtime_id: str
    version: str
    description: str
    agents: list[MCPAgentContract]

    @model_validator(mode="after")
    def _validate_unique_agents(self) -> "MCPRuntimeConfig":
        agent_ids = [agent.agent_id for agent in self.agents]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("agent_id values must be unique")
        return self


class MCPInvokeRequest(BaseModel):
    agent_id: AGENT_IDS
    capability: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    resource_uri: str | None = None


class MCPInvokeResponse(BaseModel):
    job_id: str
    status: Literal["queued"]
    agent_id: AGENT_IDS
    capability: str
    resource_uri: str | None = None
    accepted_at: datetime
    message: str


class MCPInfoResponse(BaseModel):
    runtime_id: str
    version: str
    config_path: str
    agent_count: int
    agent_ids: list[str]
    tool_scopes: list[str]
    resource_uris: list[str]
    bearer_token_required: bool


def _config_path() -> Path:
    return Path(__file__).resolve().with_name("mcp.json")


@lru_cache(maxsize=1)
def load_config() -> MCPRuntimeConfig:
    path = _config_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return MCPRuntimeConfig.model_validate(payload)


def _check_shared_token(authorization: str | None) -> None:
    expected = os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid_bearer_token")


def _agent_for(agent_id: str) -> MCPAgentContract:
    config = load_config()
    for agent in config.agents:
        if agent.agent_id == agent_id:
            return agent
    raise HTTPException(status_code=404, detail="agent_not_found")


def _resource_uri_allowed(resource_uri: str, allowed_uris: list[str]) -> bool:
    for allowed_uri in allowed_uris:
        if resource_uri == allowed_uri:
            return True
        if allowed_uri.endswith("/") and resource_uri.startswith(allowed_uri):
            return True
    return False


def _collect_unique(values: list[list[str]]) -> list[str]:
    seen: list[str] = []
    for group in values:
        for item in group:
            if item not in seen:
                seen.append(item)
    return seen


app = FastAPI(title="MEA MCP Contract Stub")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/mcp/info", response_model=MCPInfoResponse)
def mcp_info() -> MCPInfoResponse:
    config = load_config()
    return MCPInfoResponse(
        runtime_id=config.runtime_id,
        version=config.version,
        config_path=str(_config_path()),
        agent_count=len(config.agents),
        agent_ids=[agent.agent_id for agent in config.agents],
        tool_scopes=_collect_unique([agent.tool_scopes for agent in config.agents]),
        resource_uris=_collect_unique([agent.resource_uris for agent in config.agents]),
        bearer_token_required=bool(os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()),
    )


@app.get("/mcp/agents", response_model=list[MCPAgentContract])
def mcp_agents() -> list[MCPAgentContract]:
    return load_config().agents


@app.post("/mcp/invoke", response_model=MCPInvokeResponse)
def mcp_invoke(
    request: MCPInvokeRequest,
    authorization: str | None = Header(default=None),
) -> MCPInvokeResponse:
    _check_shared_token(authorization)
    agent = _agent_for(request.agent_id)
    if request.capability not in agent.capabilities:
        raise HTTPException(status_code=422, detail="capability_not_permitted")
    if request.resource_uri and not _resource_uri_allowed(request.resource_uri, agent.resource_uris):
        raise HTTPException(status_code=422, detail="resource_uri_not_permitted")

    return MCPInvokeResponse(
        job_id=f"mcp-{uuid.uuid4().hex[:12]}",
        status="queued",
        agent_id=request.agent_id,
        capability=request.capability,
        resource_uri=request.resource_uri,
        accepted_at=datetime.now(UTC),
        message="MCP contract stub accepted the invocation. Wire a real executor to replace this synthetic receipt.",
    )
