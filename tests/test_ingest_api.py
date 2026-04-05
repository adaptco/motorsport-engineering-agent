from pathlib import Path

from fastapi.testclient import TestClient

from control_plane.app import app


client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def test_list_ingest_sources():
    response = client.get("/ingest/sources")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["vendor"] == "iracing" for item in payload)


def test_normalize_endpoint(tmp_path: Path):
    response = client.post(
        "/ingest/normalize",
        json={
            "input_path": str(FIXTURES / "sample_export.csv"),
            "output_dir": str(tmp_path),
            "vendor_hint": "csv_export",
            "session_id": "api-test",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "complete"
    assert payload["vendor"] == "csv_export"
    assert payload["row_count"] == 4
