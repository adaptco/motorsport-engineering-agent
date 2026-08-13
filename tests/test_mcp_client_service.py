from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from control_plane.services import mcp_client
from shared.circuit_breaker import CircuitBreakerOpenError


def test_call_mcp_tool_success(monkeypatch) -> None:
    fake_resp = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"result": "tool_executed", "output": {"data": 123}},
    )
    post_mock = MagicMock(return_value=fake_resp)
    monkeypatch.setattr("requests.post", post_mock)
    monkeypatch.setattr(mcp_client, "MCP_SHARED_BEARER_TOKEN", "test-token")

    result = mcp_client.call_mcp_tool("mea_ci_guardrail", {"arg1": "val1"})
    assert result == {"result": "tool_executed", "output": {"data": 123}}

    post_mock.assert_called_once()
    _, kwargs = post_mock.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"
    assert kwargs["json"] == {"name": "mea_ci_guardrail", "arguments": {"arg1": "val1"}}


def test_call_mcp_tool_without_auth_header(monkeypatch) -> None:
    fake_resp = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"result": "ok"},
    )
    post_mock = MagicMock(return_value=fake_resp)
    monkeypatch.setattr("requests.post", post_mock)
    monkeypatch.setattr(mcp_client, "MCP_SHARED_BEARER_TOKEN", "")

    result = mcp_client.call_mcp_tool("status_check")
    assert result == {"result": "ok"}
    _, kwargs = post_mock.call_args
    assert "Authorization" not in kwargs["headers"]


def test_call_mcp_tool_retry_and_eventual_failure(monkeypatch) -> None:
    post_mock = MagicMock(side_effect=ConnectionError("Connection refused"))
    monkeypatch.setattr("requests.post", post_mock)
    monkeypatch.setattr(mcp_client, "MCP_API_MAX_RETRIES", 2)

    with pytest.raises(RuntimeError, match="mcp_call_failed_after_2_attempts"):
        mcp_client.call_mcp_tool("failing_tool")

    assert post_mock.call_count == 2


def test_call_mcp_tool_circuit_breaker_open(monkeypatch) -> None:
    def _open_breaker_call(func):
        raise CircuitBreakerOpenError("Circuit is open")

    monkeypatch.setattr(mcp_client.MCP_API_BREAKER, "call", _open_breaker_call)

    with pytest.raises(CircuitBreakerOpenError, match="Circuit is open"):
        mcp_client.call_mcp_tool("any_tool")
