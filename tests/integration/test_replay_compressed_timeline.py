"""tests/integration/test_replay_compressed_timeline module."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from control_plane.app import app


client = TestClient(app)


def test_session_replay_endpoint_validates_monotonic_timeline(tmp_path: Path):
    path = tmp_path / 'timeline.jsonl'
    frames = [
        {
            'session_id': 's1', 'driver_id': 'd1', 'track_id': 't1', 'car_id': 'c1',
            'timestamp_ns': 100, 'tick': 1, 'channels': {'Throttle': 0.5, 'Brake': 0.0, 'Speed': 10.0}, 'quality_flags': {}
        },
        {
            'session_id': 's1', 'driver_id': 'd1', 'track_id': 't1', 'car_id': 'c1',
            'timestamp_ns': 200, 'tick': 2, 'channels': {'Throttle': 0.5, 'Brake': 0.0, 'Speed': 11.0}, 'quality_flags': {}
        },
    ]
    path.write_text(''.join(json.dumps(f) + '\n' for f in frames), encoding='utf-8')

    response = client.post('/session/replay', json={'artifact_path': str(path), 'sampling_hz': 60, 'source': 'jsonl'})
    assert response.status_code == 200, response.text
    body = response.json()
    names = {task['name']: task['status'] for task in body['tasks']}
    assert names['jsonl_schema_valid'] == 'pass'
    assert names['timestamp_monotonicity'] == 'pass'
