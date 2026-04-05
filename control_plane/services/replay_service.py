from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable, List, Literal, TYPE_CHECKING

from pydantic import ValidationError

from shared.models import (
    DirectStreamProbeResult,
    ReplayMetrics,
    ReplayRequest,
    ReplayResponse,
    ReplayTask,
    TelemetryFrame,
)

if TYPE_CHECKING:
    from shared.models import JSONLValidationResult

def load_replay_log(path: Path) -> Iterable[TelemetryFrame]:
    with open(path, "r") as f:
        for line in f:
            if not line.strip():
                continue
            yield TelemetryFrame.model_validate_json(line)


def build_replay_metrics(path: Path) -> ReplayMetrics:
    metrics = ReplayMetrics()
    first_ts = 0
    previous_ts = 0

    try:
        for frame in load_replay_log(path):
            metrics.frames_seen += 1
            metrics.frames_valid += 1

            ts = frame.timestamp_ns
            if first_ts == 0:
                first_ts = ts

            if previous_ts > 0 and ts <= previous_ts:
                metrics.out_of_order_frames += 1

            previous_ts = ts

    except ValidationError:
        metrics.frames_seen += 1
        metrics.frames_invalid += 1
    except Exception:
        metrics.frames_invalid += 1

    if metrics.frames_valid > 1:
        metrics.duration_ns = previous_ts - first_ts
        metrics.average_hz = round((metrics.frames_valid - 1) * 1_000_000_000 / metrics.duration_ns, 2)
    return metrics


def replay_artifact(req: ReplayRequest) -> ReplayResponse:
    metrics = build_replay_metrics(Path(req.artifact_path))
    return ReplayResponse(
        replay_id=str(uuid.uuid4()),
        status="complete",
        metrics=metrics,
        tasks=build_validation_tasks(metrics, req.sampling_hz)
    )


def build_validation_tasks(metrics: ReplayMetrics, target_hz: int, validation: JSONLValidationResult | None = None) -> List[ReplayTask]:
    tasks: List[ReplayTask] = []

    def add(name: str, status: Literal["pass", "fail", "warn"], detail: str) -> None:
        tasks.append(ReplayTask(task_id=str(uuid.uuid4()), name=name, status=status, detail=detail))

    add(
        "jsonl_schema_valid",
        "pass" if metrics.frames_invalid == 0 and (validation is None or validation.invalid_lines == 0) else "fail",
        f"{metrics.frames_valid} valid frames, {metrics.frames_invalid} invalid frames",
    )

    if metrics.duration_ns > 0:
        add(
            "sample_rate_check",
            "pass" if metrics.average_hz >= target_hz * 0.9 else "warn",
            f"Average sample rate: {metrics.average_hz} Hz (Target: {target_hz} Hz)",
        )

    add(
        "timestamp_monotonicity",
        "pass" if metrics.out_of_order_frames == 0 else "fail",
        f"{metrics.out_of_order_frames} frames out of order",
    )

    return tasks


def probe_direct_stream(req: ReplayRequest) -> DirectStreamProbeResult:
    # Simplified mock implementation
    return DirectStreamProbeResult(
        session_id=Path(req.artifact_path).name,
        is_active=True,
        bitrate_kbps=1500.0,
        frame_rate_hz=60.0
    )
