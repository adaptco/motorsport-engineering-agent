from fastapi.testclient import TestClient

from mcp_server.app import app


client = TestClient(app)


def test_provider_registry_lists_required_env_vars(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.get("/providers")
    assert response.status_code == 200
    providers = {row["provider"]: row for row in response.json()}
    assert providers["openai"]["env_var"] == "OPENAI_API_KEY"
    assert providers["openai"]["configured"] is False


def test_a2a_invoke_returns_scaffold_metadata(monkeypatch):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    response = client.post(
        "/a2a/invoke",
        headers={"Authorization": "Bearer secret"},
        json={"provider": "openai", "model": "gpt-4.1", "prompt": "hello"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "scaffolded"
    assert body["required_env"] == "OPENAI_API_KEY"


def test_tools_call_supports_ralph_wiggum_agent(monkeypatch):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    response = client.post(
        "/tools/call",
        headers={"Authorization": "Bearer secret"},
        json={"name": "ralph_wiggum_agent", "arguments": {"mode": "metadata"}},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["agent_id"] == "ralph-wiggum"
    assert body["provider_agnostic"] is True
