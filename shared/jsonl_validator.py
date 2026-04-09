"""shared/jsonl_validator module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from shared.models import JSONLValidationResult, TelemetryFrame


def validate_jsonl_artifact(
    path: str | Path, *, required_fields: list[str] | None = None
) -> JSONLValidationResult:
    required_fields = required_fields or [
        "session_id",
        "driver_id",
        "track_id",
        "car_id",
        "timestamp_ns",
        "tick",
        "channels",
    ]
    artifact = Path(path)
    result = JSONLValidationResult(artifact_path=str(artifact))
    previous_timestamp_ns: int | None = None
    previous_tick: int | None = None

    with artifact.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            result.lines_seen += 1
            if not line.strip():
                result.invalid_lines += 1
                result.violations.append(f"line:{idx}:empty")
                continue
            try:
                payload: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError as exc:
                result.invalid_lines += 1
                result.violations.append(f"line:{idx}:json_decode:{exc.msg}")
                continue

            missing = [field for field in required_fields if field not in payload]
            if missing:
                result.invalid_lines += 1
                result.missing_fields.extend([f"{idx}:{field}" for field in missing])
                result.violations.append(f"line:{idx}:missing:{','.join(missing)}")
                continue

            try:
                frame = TelemetryFrame.model_validate(payload)
            except ValidationError as exc:
                result.invalid_lines += 1
                result.violations.append(f"line:{idx}:schema:{exc.errors()[0]['type']}")
                continue

            result.valid_lines += 1
            if previous_timestamp_ns is not None and frame.timestamp_ns < previous_timestamp_ns:
                result.monotonic_timestamp_ns = False
                result.violations.append(f"line:{idx}:timestamp_regressed")
            if previous_tick is not None and frame.tick <= previous_tick:
                result.monotonic_tick = False
                result.violations.append(f"line:{idx}:tick_not_strict")
            previous_timestamp_ns = frame.timestamp_ns
            previous_tick = frame.tick

    return result
