from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ingest.iracing_stream import (
    IRacingUnavailableError,
    dump_stream_to_jsonl,
    frame_from_iracing,
    load_pyirsdk,
    stream_iracing_frames,
)
from shared.models import TelemetryFrame


def fake_frames():
    for i in range(4):
        # include a duplicate timestamp
        ts = 16_666_667 if i == 1 else i * 16_666_667
        yield TelemetryFrame(
            session_id="s1",
            driver_id="d1",
            track_id="t1",
            car_id="c1",
            timestamp_ns=ts,
            tick=i * 2,  # tick gap = 2
            channels={"Throttle": 0.1 * i, "Brake": 0.0, "Speed": 50 + i},
            quality_flags={},
        )


def test_dump_stream_to_jsonl(tmp_path: Path) -> None:
    out = tmp_path / "dump.jsonl"
    metrics = dump_stream_to_jsonl(fake_frames(), out, max_frames=4)
    assert metrics.frames_valid == 4
    assert metrics.duplicate_timestamps >= 1
    assert metrics.max_tick_gap == 2
    assert metrics.average_hz > 0
    assert out.exists()
    assert out.read_text(encoding="utf-8").count("\n") == 4


def test_load_pyirsdk(monkeypatch) -> None:
    # 1. Missing module raises IRacingUnavailableError
    def _mock_import(name, *args, **kwargs):
        if name == "irsdk":
            raise ImportError("no irsdk")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _mock_import)
    with pytest.raises(IRacingUnavailableError, match="pyirsdk is not installed"):
        load_pyirsdk()


def test_frame_from_iracing() -> None:
    fake_ir = {
        "Throttle": [0.75],
        "Brake": 0.25,
        "Speed": 100,
    }
    channel_map = {
        "throttle": "Throttle",
        "brake": "Brake",
        "speed": "Speed",
    }
    frame = frame_from_iracing(fake_ir, channel_map, "session-123", 5)
    assert frame.session_id == "session-123"
    assert frame.tick == 5
    assert frame.channels["throttle"] == 0.75
    assert frame.channels["brake"] == 0.25
    assert frame.channels["speed"] == 100


def test_stream_iracing_frames(monkeypatch) -> None:
    mock_ir = MagicMock()
    mock_ir.is_initialized = True
    mock_ir.is_connected = True
    mock_ir.__getitem__.side_effect = lambda k: 0.5

    mock_irsdk_cls = MagicMock()
    mock_irsdk_cls.IRSDK.return_value = mock_ir

    monkeypatch.setattr("ingest.iracing_stream.load_pyirsdk", lambda: mock_irsdk_cls)

    # Take first 2 frames from generator
    gen = stream_iracing_frames({"throttle": "Throttle"}, sampling_hz=100)
    frame1 = next(gen)
    frame2 = next(gen)

    assert frame1.channels["throttle"] == 0.5
    assert frame2.tick == 1
    gen.close()
    mock_ir.shutdown.assert_called_once()
