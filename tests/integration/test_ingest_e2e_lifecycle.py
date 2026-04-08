from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from control_plane.app import app
from control_plane.routes import runtime_logs


def test_ingest_to_runtime_debrief_lifecycle(tmp_path: Path, monkeypatch) -> None:
    raw_log = tmp_path / "session_export.csv"
    raw_log.write_text(
        "\n".join(
            [
                "Time,Speed,Throttle,Brake",
                "0.0,10,20,0",
                "1.0,12,25,0",
            ]
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "normalized"
    runtime_dir = tmp_path / "runtime_logs"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runtime_logs, "LOG_DIR", runtime_dir)

    with TestClient(app) as client:
        normalize_response = client.post(
            "/ingest/normalize",
            json={
                "input_path": str(raw_log),
                "output_dir": str(output_dir),
                "vendor_hint": "csv_export",
                "session_id": "e2e-session",
            },
        )
        assert normalize_response.status_code == 200
        normalized_csv = normalize_response.json()["normalized_csv"]
        assert Path(normalized_csv).exists()

        with Path(normalized_csv).open("rb") as normalized_handle:
            parse_response = client.post(
                "/runtime/logs/parse",
                files={"file": ("normalized_channels.csv", normalized_handle, "text/csv")},
            )
        assert parse_response.status_code == 200
        session_id = parse_response.json()["summary"]["session_id"]

        debrief_response = client.get(f"/runtime/sessions/{session_id}/debrief")
        assert debrief_response.status_code == 200
        debrief = debrief_response.json()
        assert debrief["session_id"] == session_id
        assert debrief["row_count"] >= 2
