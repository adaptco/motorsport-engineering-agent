from __future__ import annotations

from fastapi.testclient import TestClient

import control_plane.app as app_module


def test_rate_limit_blocks_excess_post_requests(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_module, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(app_module, "RATE_LIMIT_REQUESTS_PER_WINDOW", 1)
    monkeypatch.setattr(app_module, "RATE_LIMIT_PATHS", {"/repos/fix-ci"})
    app_module._rate_limit_buckets.clear()
    app_module._metrics["requests_total"] = 0
    app_module._metrics["rate_limited_total"] = 0

    monkeypatch.setattr(app_module, "create_job", lambda *_args, **_kwargs: "job-1")
    monkeypatch.setattr(app_module, "enqueue", lambda _job: None)

    payload = {"repo": "adaptco/motorsport-engineering-agent", "branch": "main", "patch": "diff --git a b"}
    with TestClient(app_module.app) as client:
        first = client.post("/repos/fix-ci", json=payload)
        second = client.post("/repos/fix-ci", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert first.headers.get("x-request-id")
    metrics = app_module.metrics()
    assert "mea_requests_total" in metrics
