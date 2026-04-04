
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

from shared.models import ReplayMetrics, TelemetryFrame


class IRacingUnavailableError(RuntimeError):
    pass


def load_pyirsdk():
    try:
        import irsdk  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised only in Windows env
        raise IRacingUnavailableError("pyirsdk is not installed or iRacing is unavailable") from exc
    return irsdk


def frame_from_iracing(ir, channel_map: Dict[str, str], session_id: str, tick: int) -> TelemetryFrame:
    channels: Dict[str, float | int] = {}
    for canonical, source in channel_map.items():
        value = ir[source]
        if isinstance(value, (list, tuple)):
            value = value[0]
        channels[canonical] = float(value) if isinstance(value, float) else int(value) if isinstance(value, int) else float(value)
    return TelemetryFrame(
        session_id=session_id,
        driver_id="iracing_driver",
        track_id="unknown",
        car_id="unknown",
        timestamp_ns=time.monotonic_ns(),
        tick=tick,
        channels=channels,
        quality_flags={},
    )


def stream_iracing_frames(channel_map: Dict[str, str], sampling_hz: int = 60) -> Iterator[TelemetryFrame]:
    irsdk = load_pyirsdk()
    ir = irsdk.IRSDK()
    ir.startup()
    tick = 0
    dt = 1.0 / sampling_hz
    session_id = f"iracing-{int(time.time())}"
    try:  # pragma: no cover - requires live simulator
        while not ir.is_initialized or not ir.is_connected:
            time.sleep(0.25)
            ir.freeze_var_buffer_latest()
        while True:
            ir.freeze_var_buffer_latest()
            yield frame_from_iracing(ir, channel_map, session_id, tick)
            tick += 1
            time.sleep(dt)
    finally:
        ir.shutdown()


def dump_stream_to_jsonl(frames: Iterable[TelemetryFrame], output_path: Path, max_frames: Optional[int] = None) -> ReplayMetrics:
    metrics = ReplayMetrics()
    previous_ts: Optional[int] = None
    previous_tick: Optional[int] = None
    with output_path.open("w", encoding="utf-8") as handle:
        for index, frame in enumerate(frames, start=1):
            if max_frames is not None and index > max_frames:
                break
            handle.write(frame.model_dump_json() + "\n")
            metrics.frames_seen += 1
            metrics.frames_valid += 1
            if previous_ts is not None:
                if previous_ts == frame.timestamp_ns:
                    metrics.duplicate_timestamps += 1
                metrics.duration_ns = max(metrics.duration_ns, frame.timestamp_ns - previous_ts)
            if previous_tick is not None:
                metrics.max_tick_gap = max(metrics.max_tick_gap, frame.tick - previous_tick)
            previous_ts = frame.timestamp_ns
            previous_tick = frame.tick
    if metrics.frames_valid > 1 and metrics.duration_ns > 0:
        metrics.average_hz = round((metrics.frames_valid - 1) * 1_000_000_000 / metrics.duration_ns, 2)
    return metrics
