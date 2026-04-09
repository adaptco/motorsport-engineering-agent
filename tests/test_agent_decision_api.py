"""tests/test_agent_decision_api module."""

from fastapi.testclient import TestClient

from control_plane.app import app

client = TestClient(app)


def test_agent_decision_endpoint_returns_supervisor_metadata(tmp_path, monkeypatch):
    ledger_path = tmp_path / "agent-ledger.db"
    monkeypatch.setenv("SESSION_LEDGER_DB_PATH", str(ledger_path))
    monkeypatch.setattr("control_plane.routes.agent.LEDGER_DB_PATH", str(ledger_path))
    response = client.post(
        "/agent/decision",
        json={
            "session_id": "s-1",
            "run_id": "r-1",
            "trace_id": "t-1",
            "prompt": "Assess brake trace for lap 14.",
            "provider": "openai",
            "model": "gpt-4.1",
            "metadata": {"mode": "sentry"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["queued_job"] == "supervisor_decision"
    assert body["required_env"] == "OPENAI_API_KEY"
