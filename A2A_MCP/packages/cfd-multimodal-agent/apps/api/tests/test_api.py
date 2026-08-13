from cfd_api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simulate():
    response = client.post(
        "/simulate",
        json={
            "preset_id": "gt",
            "speed_kph": 100,
            "yaw_deg": 0,
            "ride_height_mm": 55,
            "rear_wing": 8,
            "design_notes": "baseline concept",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["speed_mps"] > 0
    assert len(body["pressure_map"]) == 48
    assert "Vehicle concept" in body["prompt_pack"]
