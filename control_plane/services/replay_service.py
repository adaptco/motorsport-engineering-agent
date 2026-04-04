from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Iterable, List, Literal

from pydantic import ValidationError

from shared.jsonl_validator import validate_jsonl_artifact
from shared.models import (
    DirectStreamProbeResult,
    JSONLValidationResult,
    ReplayMetrics,
    ReplayRequest,
    ReplayResponse,
    ReplayTask,
    TelemetryFrame,
)

REQUIRED_CHANNELS = ("Throttle", "Brake", "Speed")


def iter_jsonl_frames(path: Path, max_frames: int | None = None) -> Iterable[TelemetryFrame]:
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if max_frames and idx > max_frames:
                break
            yield TelemetryFrame.model_validate(json.loads(line))


def build_replay_metrics(path: Path, max_frames: int | None = None) -> ReplayMetrics:
    metrics = ReplayMetrics()
    previous_tick: int | None = None
    first_ts: int | None = None
    previous_ts: int | None = None

    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if max_frames and idx > max_frames:
                break
            metrics.frames_seen += 1
            try:
                frame = TelemetryFrame.model_validate(json.loads(line))
            except (json.JSONDecodeError, ValidationError):
                metrics.frames_invalid += 1
                continue

            metrics.frames_valid += 1
            if first_ts is None:
                first_ts = frame.timestamp_ns
            if previous_tick is not None:
                metrics.max_tick_gap = max(metrics.max_tick_gap, frame.tick - previous_tick)
            if previous_ts is not None:
                if frame.timestamp_ns == previous_ts:
                    metrics.duplicate_timestamps += 1
            previous_tick = frame.tick
            previous_ts = frame.timestamp_ns

            missing = [ch for ch in REQUIRED_CHANNELS if ch not in frame.channels]
            for channel in missing:
                if channel not in metrics.missing_required_channels:
                    metrics.missing_required_channels.append(channel)

    if metrics.frames_valid > 1 and first_ts is not None and previous_ts is not None and previous_ts > first_ts:
        metrics.duration_ns = previous_ts - first_ts
        metrics.average_hz = round((metrics.frames_valid - 1) * 1_000_000_000 / metrics.duration_ns, 2)
    return metrics


def build_validation_tasks(metrics: ReplayMetrics, target_hz: int, validation: JSONLValidationResult | None = None) -> List[ReplayTask]:
    tasks: List[ReplayTask] = []

    def add(name: str, status: Literal["pass", "fail", "warn"], detail: str) -> None:
        tasks.append(ReplayTask(task_id=str(uuid.uuid4()), name=name, status=status, detail=detail))

    add(
        "jsonl_schema_valid",
        "pass" if metrics.frames_invalid == 0 and (validation is None or validation.invalid_lines == 0) else "fail",
        f"{metrics.frames_valid} valid frames, {metrics.frames_invalid} invalid frames",
    )
    add(
        "tick_ordering",
        "pass" if metrics.max_tick_gap <= 1 and (validation is None or validation.monotonic_tick) else "warn",
        f"Maximum tick gap was {metrics.max_tick_gap}",
    )
    if metrics.average_hz == 0:
        hz_status: Literal["pass", "fail", "warn"] = "fail"
    elif abs(metrics.average_hz - target_hz) <= 5:
        hz_status = "pass"
    else:
        hz_status = "warn"
    add(
        "sampling_rate",
        hz_status,
        f"Observed {metrics.average_hz}Hz against target {target_hz}Hz",
    )
    add(
        "timestamp_uniqueness",
        "pass" if metrics.duplicate_timestamps == 0 else "warn",
        f"{metrics.duplicate_timestamps} duplicate timestamps observed",
    )
    add(
        "required_channels",
        "pass" if not metrics.missing_required_channels else "fail",
        "Missing channels: " + ", ".join(metrics.missing_required_channels) if metrics.missing_required_channels else "All required channels present",
    )
    if validation is not None:
        add(
            "timestamp_monotonicity",
            "pass" if validation.monotonic_timestamp_ns else "fail",
            "timestamps monotonic" if validation.monotonic_timestamp_ns else "; ".join(v for v in validation.violations if 'timestamp' in v),
        )
    return tasks


def replay_artifact(request: ReplayRequest) -> ReplayResponse:
    path = Path(request.artifact_path)
    metrics = build_replay_metrics(path, max_frames=request.max_frames)
    validation = validate_jsonl_artifact(path) if request.source == 'jsonl' else None
    tasks = build_validation_tasks(metrics, request.sampling_hz, validation=validation)
    return ReplayResponse(
        replay_id=str(uuid.uuid4()),
        status="complete",
        metrics=metrics,
        tasks=tasks,
    )


def direct_stream_probe(metrics: ReplayMetrics, target_hz: int, notes: list[str] | None = None) -> DirectStreamProbeResult:
    tasks = build_validation_tasks(metrics, target_hz)
    return DirectStreamProbeResult(status="complete", metrics=metrics, tasks=tasks, notes=notes or [])
