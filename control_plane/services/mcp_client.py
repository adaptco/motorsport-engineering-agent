"""control_plane/services/mcp_client module."""

from __future__ import annotations

import os
from typing import Any

import requests

from shared.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

MCP_SERVER_BASE_URL = os.environ.get("MCP_SERVER_BASE_URL", "http://localhost:7000").rstrip("/")
MCP_SHARED_BEARER_TOKEN = os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()
MCP_API_MAX_RETRIES = int(os.environ.get("MCP_API_MAX_RETRIES", "2"))
MCP_API_BREAKER = CircuitBreaker.from_env("MCP_API")


def call_mcp_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"name": name, "arguments": arguments or {}}
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if MCP_SHARED_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_SHARED_BEARER_TOKEN}"

    def _request() -> dict[str, Any]:
        response = requests.post(
            f"{MCP_SERVER_BASE_URL}/tools/call",
            json=body,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    attempts = max(1, MCP_API_MAX_RETRIES)
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return MCP_API_BREAKER.call(_request)
        except CircuitBreakerOpenError:
            raise
        except Exception as exc:
            last_exc = exc
    raise RuntimeError(f"mcp_call_failed_after_{attempts}_attempts:{name}:{last_exc}")
