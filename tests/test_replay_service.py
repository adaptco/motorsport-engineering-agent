"""tests/test_replay_service module."""


import json
from pathlib import Path

from control_plane.services.replay_service import replay_artifact
from shared.models import ReplayRequest


def _write_frame(path: Path, tick: int, timestamp_ns: int, speed: float = 40.0):
    path.write_text(path.read_text(encoding="utf-8") + json.dumps({
        "session_id": "s1",
        "driver_id": "d1",
        "track_id": "t1",
        "car_id": "c1",
        "timestamp_ns": timestamp_ns,
        "tick": tick,
        "channels": {"Throttle": 0.5, "Brake": 0.0, "Speed": speed},
        "quality_flags": {},
    }) + "\n", encoding="utf-8")


def test_replay_artifact_produces_metrics_and_tasks(tmp_path: Path):
    path = tmp_path / "artifact.jsonl"
    path.write_text("", encoding="utf-8")
    _write_frame(path, 0, 0)
    _write_frame(path, 1, 16_666_667)
    _write_frame(path, 2, 33_333_334)

    response = replay_artifact(ReplayRequest(artifact_path=str(path), sampling_hz=60))
    assert response.metrics.frames_valid == 3
    assert any(task.name == "jsonl_schema_valid" for task in response.tasks)
    assert response.status == "complete"
