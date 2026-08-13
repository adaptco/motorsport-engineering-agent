"""tests/integration/test_ingest_runtime_debrief_e2e module."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from control_plane.app import app
from control_plane.routes import runtime_logs


def test_normalize_to_runtime_debrief_lifecycle(tmp_path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime_logs"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runtime_logs, "LOG_DIR", runtime_dir)

    output_dir = tmp_path / "normalized"
    source_csv = Path("tests/fixtures/sample_export.csv").resolve()
    assert source_csv.exists()

    with TestClient(app) as client:
        normalize_resp = client.post(
            "/ingest/normalize",
            json={
                "input_path": str(source_csv),
                "output_dir": str(output_dir),
                "vendor_hint": "csv_export",
            },
        )
        assert normalize_resp.status_code == 200, normalize_resp.text
        normalized_csv = normalize_resp.json()["normalized_csv"]

        parse_resp = client.post(
            "/runtime/logs/parse",
            files={"file": ("normalized.csv", Path(normalized_csv).read_bytes(), "text/csv")},
        )
        assert parse_resp.status_code == 200, parse_resp.text
        session_id = parse_resp.json()["summary"]["session_id"]

        sessions_resp = client.get("/runtime/sessions")
        assert sessions_resp.status_code == 200, sessions_resp.text
        assert any(item["session_id"] == session_id for item in sessions_resp.json())

        debrief_resp = client.get(f"/runtime/sessions/{session_id}/debrief")
        assert debrief_resp.status_code == 200, debrief_resp.text
        payload = debrief_resp.json()
        assert payload["session_id"] == session_id
        assert payload["row_count"] > 0
