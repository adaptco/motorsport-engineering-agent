from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from mcp_server.app import app
from mcp_server.routes import runtime_state


def _client_with_tmp_ledger(tmp_path: Path) -> TestClient:
    runtime_state.SESSION_LEDGER_DB_PATH = tmp_path / "runtime-state-ledger.db"
    runtime_state._SNAPSHOT_CACHE.clear()
    return TestClient(app)


def test_runtime_state_event_post_and_snapshot(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    client = _client_with_tmp_ledger(tmp_path)
    headers = {"Authorization": "Bearer secret"}

    event = {
        "idempotency_key": "agent-1",
        "session_id": "sess-1",
        "event_type": "agent_upsert",
        "payload": {
            "agent_id": "agent.alpha",
            "display_name": "Alpha",
            "runtime": "local",
            "host": "localhost",
            "branch": "feature/runtime",
            "commit_hash": "abcdef1",
            "note": "boot"
        },
    }
    post = client.post("/runtime-state/events", headers=headers, json=event)
    assert post.status_code == 200, post.text
    body = post.json()
    assert body["status"] == "accepted"
    assert body["applied_seq"] == 1

    snapshot = client.get("/runtime-state/snapshot?session_id=sess-1", headers=headers)
    assert snapshot.status_code == 200, snapshot.text
    snap = snapshot.json()
    assert snap["last_seq"] == 1
    assert snap["agents"]["agent.alpha"]["branch"] == "feature/runtime"
    assert snap["agents"]["agent.alpha"]["commit_hash"] == "abcdef1"


def test_runtime_state_idempotency_duplicate(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    client = _client_with_tmp_ledger(tmp_path)
    headers = {"Authorization": "Bearer secret"}

    payload = {
        "idempotency_key": "same-key",
        "session_id": "sess-dup",
        "event_type": "task_upsert",
        "payload": {
            "task_id": "TASK-1",
            "title": "Write tests",
            "state": "running",
        },
    }
    first = client.post("/runtime-state/events", headers=headers, json=payload)
    second = client.post("/runtime-state/events", headers=headers, json=payload)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"
    assert second.json()["applied_seq"] == first.json()["applied_seq"]


def test_runtime_state_commit_hash_normalization(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    client = _client_with_tmp_ledger(tmp_path)
    headers = {"Authorization": "Bearer secret"}

    post = client.post(
        "/runtime-state/events",
        headers=headers,
        json={
            "idempotency_key": "invalid-hash",
            "session_id": "sess-invalid",
            "event_type": "agent_upsert",
            "payload": {
                "agent_id": "agent.bad",
                "runtime": "cloud",
                "commit_hash": "not-a-hash",
            },
        },
    )
    assert post.status_code == 200, post.text

    snap = client.get("/runtime-state/snapshot?session_id=sess-invalid", headers=headers).json()
    assert snap["agents"]["agent.bad"]["commit_hash"] == "INVALID_HASH"
    assert snap["agents"]["agent.bad"]["dirty"] is True


def test_runtime_state_events_and_stream_resume(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MCP_SHARED_BEARER_TOKEN", "secret")
    client = _client_with_tmp_ledger(tmp_path)
    headers = {"Authorization": "Bearer secret"}

    for idx in range(1, 4):
        response = client.post(
            "/runtime-state/events",
            headers=headers,
            json={
                "idempotency_key": f"event-{idx}",
                "session_id": "sess-stream",
                "event_type": "task_upsert",
                "payload": {"task_id": f"T-{idx}", "state": "queued"},
            },
        )
        assert response.status_code == 200, response.text

    events = client.get("/runtime-state/events?session_id=sess-stream&after_seq=1", headers=headers)
    assert events.status_code == 200, events.text
    body = events.json()
    seqs = [evt["seq"] for evt in body["events"]]
    assert seqs == [2, 3]

    with client.stream(
        "GET",
        "/runtime-state/stream?session_id=sess-stream&after_seq=1&once=true&access_token=secret",
        headers={"Accept": "text/event-stream"},
    ) as stream_response:
        assert stream_response.status_code == 200
        found_payload = None
        for line in stream_response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            found_payload = json.loads(line.replace("data: ", "", 1))
            if found_payload.get("seq") == 3:
                break
        assert found_payload is not None
        assert found_payload["seq"] == 3
