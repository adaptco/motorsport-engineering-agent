"""tests/test_api_v32 module."""

from pathlib import Path

from fastapi.testclient import TestClient

from control_plane.app import app
from shared.forensic_ledger import get_session_head


client = TestClient(app)


def test_verifier_route_writes_paired_receipts(tmp_path: Path, monkeypatch):
    ledger_path = tmp_path / "ledger.db"
    monkeypatch.setenv("SESSION_LEDGER_DB_PATH", str(ledger_path))
    monkeypatch.setattr("control_plane.routes.verifier.LEDGER_DB_PATH", str(ledger_path))

    response = client.post(
        "/verifier/execute",
        json={
            "principal_id": "agent_01",
            "session_id": "session-1",
            "run_id": "run-1",
            "trace_id": "trace-1",
            "policy_version": "rbac.v1",
            "authz_scope": "read-only",
            "job_name": "verify_dir_exists",
            "params": {"path": str(tmp_path)},
            "timeout_ms": 5000,
        },
    )
    assert response.status_code == 200, response.text
    head = get_session_head(str(ledger_path), "session-1")
    assert head is not None
    assert head["last_logical_clock"] == 2
    assert head["last_status"] == "ACCEPTED"


def test_session_replay_ledger_endpoint(tmp_path: Path, monkeypatch):
    ledger_path = tmp_path / "session-ledger.db"
    monkeypatch.setenv("SESSION_LEDGER_DB_PATH", str(ledger_path))
    monkeypatch.setattr("control_plane.repository.SESSION_LEDGER_DB_PATH", str(ledger_path))

    payload = {
        "session_id": "s-1",
        "principal_id": "system",
        "policy_version": "rbac.v1",
        "authz_scope": "session:write",
        "evidence_packets": [
            {
                "evidence_packet_id": "ep-1",
                "session_id": "s-1",
                "timestamp_logical_ns": 100,
                "severity": "ADVISORY",
                "features": {"brake_delta": 1.2, "confidence": 0.9},
            }
        ],
        "recommendations": [
            {
                "recommendation_id": "rec-1",
                "evidence_packet_id": "ep-1",
                "priority": "ADVISORY",
                "action": "Brake 5m later",
            }
        ],
    }
    ingest = client.post("/session/evidence", json=payload)
    assert ingest.status_code == 200, ingest.text

    replay = client.get("/session/s-1/replay-ledger")
    assert replay.status_code == 200, replay.text
    body = replay.json()
    assert body["chain_ok"] is True
    assert len(body["receipts"]) == 1
    assert body["receipts"][0]["job_name"] == "store_session_evidence"
