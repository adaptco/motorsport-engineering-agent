from __future__ import annotations

import json
from pathlib import Path

from shared.jsonl_validator import validate_jsonl_artifact


def test_jsonl_validator_flags_missing_fields_and_regressions(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    rows = [
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "car_id": "c1",
            "timestamp_ns": 200,
            "tick": 2,
            "channels": {"Throttle": 0.1, "Brake": 0.0, "Speed": 1.0},
        },
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "timestamp_ns": 100,
            "tick": 1,
            "channels": {"Throttle": 0.1, "Brake": 0.0, "Speed": 1.0},
        },
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    result = validate_jsonl_artifact(path)
    assert result.invalid_lines == 1
    assert any("car_id" in item for item in result.missing_fields)


def test_jsonl_validator_empty_lines_and_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "malformed.jsonl"
    content = (
        "\n"
        + "{not-valid-json}\n"
        + '{"session_id": "s1", "driver_id": "d1", "track_id": "t1", "car_id": "c1", "timestamp_ns": -1, "tick": 1, "channels": {"Throttle": 1.0}}\n'
    )
    path.write_text(content, encoding="utf-8")

    result = validate_jsonl_artifact(path)
    assert result.lines_seen == 3
    assert result.invalid_lines == 3
    assert any("empty" in v for v in result.violations)
    assert any("json_decode" in v for v in result.violations)
    assert any("schema" in v for v in result.violations)


def test_jsonl_validator_monotonicity_violations(tmp_path: Path) -> None:
    path = tmp_path / "regressed.jsonl"
    rows = [
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "car_id": "c1",
            "timestamp_ns": 500,
            "tick": 5,
            "channels": {"Throttle": 0.5},
        },
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "car_id": "c1",
            "timestamp_ns": 400,
            "tick": 5,
            "channels": {"Throttle": 0.6},
        },
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    result = validate_jsonl_artifact(path)
    assert result.valid_lines == 2
    assert result.monotonic_timestamp_ns is False
    assert result.monotonic_tick is False
    assert any("timestamp_regressed" in v for v in result.violations)
    assert any("tick_not_strict" in v for v in result.violations)


def test_jsonl_validator_all_valid(tmp_path: Path) -> None:
    path = tmp_path / "valid.jsonl"
    rows = [
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "car_id": "c1",
            "timestamp_ns": 100,
            "tick": 1,
            "channels": {"Throttle": 0.0},
        },
        {
            "session_id": "s1",
            "driver_id": "d1",
            "track_id": "t1",
            "car_id": "c1",
            "timestamp_ns": 200,
            "tick": 2,
            "channels": {"Throttle": 0.5},
        },
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    result = validate_jsonl_artifact(path)
    assert result.valid_lines == 2
    assert result.invalid_lines == 0
    assert result.monotonic_timestamp_ns is True
    assert result.monotonic_tick is True
