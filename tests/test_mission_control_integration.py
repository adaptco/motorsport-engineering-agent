"""Mission Control static-surface and runtime-log integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from control_plane.app import app
from control_plane.routes import runtime_logs


def test_mission_control_static_surface_and_api_discovery() -> None:
    with TestClient(app) as client:
        index_response = client.get("/")
        assert index_response.status_code == 200
        assert "MEA Motorsport Engineering" in index_response.text
        assert 'src="/static/app.js"' in index_response.text

        page_response = client.get("/static/pages/mission-control.js")
        assert page_response.status_code == 200
        assert "RUNTIME LOG INTAKE" in page_response.text
        assert "/api/routes" in page_response.text
        assert "/runtime-state/snapshot" in page_response.text

        discovered = client.get("/api/routes")
        assert discovered.status_code == 200
        routes = discovered.json()["routes"]
        route_pairs = {(route["method"], route["path"]) for route in routes}
        assert ("GET", "/healthz") in route_pairs
        assert ("GET", "/runtime/sessions") in route_pairs
        assert ("POST", "/runtime/logs/parse") in route_pairs
        assert all(route["method"] != "HEAD" for route in routes)


def test_mission_control_runtime_log_review_flow(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(runtime_logs, "LOG_DIR", tmp_path)
    with TestClient(app) as client:
        parsed = client.post(
            "/runtime/logs/parse",
            files={
                "file": (
                    "mission-control-flow.csv",
                    b"time,speed,rpm\n0.0,120.5,6500\n0.1,121.0,6550\n",
                    "text/csv",
                )
            },
        )
        assert parsed.status_code == 200
        session_id = parsed.json()["summary"]["session_id"]

        sessions = client.get("/runtime/sessions")
        assert sessions.status_code == 200
        assert any(session["session_id"] == session_id for session in sessions.json())

        debrief = client.get(f"/runtime/sessions/{session_id}/debrief")
        assert debrief.status_code == 200
        assert debrief.json()["row_count"] == 2
        assert debrief.json()["top_columns"] == ["time", "speed", "rpm"]


def test_mission_control_cors_allows_configured_local_origin() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/routes",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"
