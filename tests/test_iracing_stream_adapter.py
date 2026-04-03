
from pathlib import Path

from ingest.iracing_stream import dump_stream_to_jsonl
from shared.models import TelemetryFrame


def fake_frames():
    for i in range(3):
        yield TelemetryFrame(
            session_id="s1",
            driver_id="d1",
            track_id="t1",
            car_id="c1",
            timestamp_ns=i * 16_666_667,
            tick=i,
            channels={"Throttle": 0.1 * i, "Brake": 0.0, "Speed": 50 + i},
            quality_flags={},
        )


def test_dump_stream_to_jsonl(tmp_path: Path):
    out = tmp_path / "dump.jsonl"
    metrics = dump_stream_to_jsonl(fake_frames(), out, max_frames=3)
    assert metrics.frames_valid == 3
    assert out.exists()
    assert out.read_text(encoding="utf-8").count("\n") == 3
