from fastapi.testclient import TestClient

from mcp_api import app


client = TestClient(app)


def test_mcp_info_reports_contract_metadata():
    response = client.get("/mcp/info")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["runtime_id"] == "motorsport-engineering-agent-mcp"
    assert body["agent_count"] == 5
    assert "planner" in body["agent_ids"]


def test_mcp_agents_exposes_declarative_registry():
    response = client.get("/mcp/agents")
    assert response.status_code == 200, response.text
    agents = {row["agent_id"]: row for row in response.json()}
    assert agents["coder"]["role"] == "coder"
    assert "implement" in agents["coder"]["capabilities"]


def test_mcp_invoke_validates_capability_pairs(monkeypatch):
    monkeypatch.delenv("MCP_SHARED_BEARER_TOKEN", raising=False)
    response = client.post(
        "/mcp/invoke",
        json={
            "agent_id": "reviewer",
            "capability": "review",
            "arguments": {"target": "README.md"},
            "resource_uri": "repo://tests/test_mcp_api.py",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["agent_id"] == "reviewer"
    assert body["job_id"].startswith("mcp-")


def test_mcp_invoke_rejects_unknown_capabilities():
    response = client.post(
        "/mcp/invoke",
        json={
            "agent_id": "tester",
            "capability": "implement",
            "arguments": {"target": "tests/test_mcp_api.py"},
        },
    )
    assert response.status_code == 422, response.text
