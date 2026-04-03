
import json
from pathlib import Path

from shared.models import TelemetryFrame
from control_plane.services.replay_service import build_replay_metrics


def test_telemetry_frame_accepts_valid_jsonl(tmp_path: Path):
    data = {
        "session_id": "s1",
        "driver_id": "d1",
        "track_id": "Road America",
        "car_id": "GT3",
        "timestamp_ns": 1_000_000_000,
        "tick": 0,
        "channels": {"Throttle": 0.5, "Brake": 0.0, "Speed": 50.0},
        "quality_flags": {},
    }
    frame = TelemetryFrame.model_validate(data)
    assert frame.channels["Speed"] == 50.0

    path = tmp_path / "artifact.jsonl"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    metrics = build_replay_metrics(path)
    assert metrics.frames_valid == 1
    assert metrics.frames_invalid == 0
