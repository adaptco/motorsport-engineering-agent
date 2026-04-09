"""tests/test_jsonl_validator module."""

import json
from pathlib import Path

from shared.jsonl_validator import validate_jsonl_artifact


def test_jsonl_validator_flags_missing_fields_and_regressions(tmp_path: Path):
    path = tmp_path / 'bad.jsonl'
    rows = [
        {'session_id': 's1', 'driver_id': 'd1', 'track_id': 't1', 'car_id': 'c1', 'timestamp_ns': 200, 'tick': 2, 'channels': {'Throttle': 0.1, 'Brake': 0.0, 'Speed': 1.0}},
        {'session_id': 's1', 'driver_id': 'd1', 'track_id': 't1', 'timestamp_ns': 100, 'tick': 1, 'channels': {'Throttle': 0.1, 'Brake': 0.0, 'Speed': 1.0}},
    ]
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    result = validate_jsonl_artifact(path)
    assert result.invalid_lines == 1
    assert any('car_id' in item for item in result.missing_fields)
