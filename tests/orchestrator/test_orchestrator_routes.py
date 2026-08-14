from __future__ import annotations

from fastapi.testclient import TestClient

from control_plane.app import app
from control_plane.routes.orchestrator import reset_orchestrator_runtime


def payload(*, idempotency_key: str = "route-key") -> dict:
    return {
        "command_type": "execution.submit",
        "idempotency_key": idempotency_key,
        "workflow_type": "repo.fix_ci",
        "priority": "normal",
        "input": {"repository": "adaptco/motorsport-engineering-agent", "target": "example"},
        "correlation": {"request_id": "req-route", "trace_id": "trace-route"},
    }


def test_command_lifecycle_and_evidence_routes_are_available() -> None:
    reset_orchestrator_runtime()
    with TestClient(app) as client:
        response = client.post("/orchestrator/commands", json=payload())
        assert response.status_code == 201
        created = response.json()
        run_id = created["execution_run_id"]
        assert created["events"][-1] == "ExecutionAttemptCreated"

        projection = client.get(f"/orchestrator/runs/{run_id}/projection")
        events = client.get(f"/orchestrator/runs/{run_id}/events")
        receipts = client.get(f"/orchestrator/runs/{run_id}/receipts")
        listing = client.get("/orchestrator/runs?status=attempt_created")

    assert projection.status_code == 200
    assert projection.json()["status"] == "attempt_created"
    assert [event["aggregate_version"] for event in events.json()["events"]] == [1, 2, 3, 4]
    assert len(receipts.json()["receipts"]) == 4
    assert listing.json()["runs"][0]["run_id"] == run_id


def test_duplicate_key_returns_canonical_result_and_conflict_is_normalized() -> None:
    reset_orchestrator_runtime()
    with TestClient(app) as client:
        first = client.post("/orchestrator/commands", json=payload())
        replay = client.post("/orchestrator/commands", json=payload())
        conflict_payload = payload()
        conflict_payload["workflow_type"] = "different.workflow"
        conflict = client.post("/orchestrator/commands", json=conflict_payload)

    assert replay.status_code == 201
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["execution_run_id"] == first.json()["execution_run_id"]
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_lease_is_bounded_and_unknown_runs_use_normalized_not_found() -> None:
    reset_orchestrator_runtime()
    with TestClient(app) as client:
        created = client.post("/orchestrator/commands", json=payload()).json()
        leased = client.post(
            f"/orchestrator/runs/{created['execution_run_id']}/leases",
            json={"executor_id": "test-agent", "ttl_seconds": 60},
        )
        duplicate_lease = client.post(
            f"/orchestrator/runs/{created['execution_run_id']}/leases",
            json={"executor_id": "other-agent", "ttl_seconds": 60},
        )
        missing = client.get("/orchestrator/runs/run_missing")

    assert leased.status_code == 200
    assert leased.json()["status"] == "leased"
    assert duplicate_lease.status_code == 409
    assert duplicate_lease.json()["detail"]["code"] == "LEASE_CONFLICT"
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "RUN_NOT_FOUND"
