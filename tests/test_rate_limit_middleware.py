from __future__ import annotations

import time
from collections import deque

from fastapi.testclient import TestClient

import control_plane.app as app_module


def test_rate_limit_blocks_excess_post_requests(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_module, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(app_module, "RATE_LIMIT_REQUESTS_PER_WINDOW", 1)
    monkeypatch.setattr(app_module, "RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(app_module, "RATE_LIMIT_PATHS", {"/repos/fix-ci"})
    monkeypatch.setattr(app_module, "TRUST_PROXY_HEADERS", False)
    app_module._rate_limit_buckets.clear()
    app_module._last_rate_limit_cleanup_at = 0.0
    app_module._metrics["requests_total"] = 0
    app_module._metrics["rate_limited_total"] = 0

    monkeypatch.setattr(app_module, "create_job", lambda *_args, **_kwargs: "job-1")
    monkeypatch.setattr(app_module, "enqueue", lambda _job: None)

    payload = {
        "repo": "adaptco/motorsport-engineering-agent",
        "branch": "main",
        "patch": "diff --git a b",
    }
    with TestClient(app_module.app) as client:
        first = client.post("/repos/fix-ci", json=payload)
        second = client.post("/repos/fix-ci", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert first.headers.get("x-request-id")
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.headers["content-type"].startswith("text/plain")
    assert "mea_requests_total" in metrics.text


def test_rate_limit_uses_remote_client_by_default(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_module, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(app_module, "RATE_LIMIT_REQUESTS_PER_WINDOW", 5)
    monkeypatch.setattr(app_module, "RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(app_module, "RATE_LIMIT_PATHS", {"/repos/fix-ci"})
    monkeypatch.setattr(app_module, "TRUST_PROXY_HEADERS", False)
    app_module._rate_limit_buckets.clear()

    monkeypatch.setattr(app_module, "create_job", lambda *_args, **_kwargs: "job-2")
    monkeypatch.setattr(app_module, "enqueue", lambda _job: None)

    payload = {
        "repo": "adaptco/motorsport-engineering-agent",
        "branch": "main",
        "patch": "diff --git a b",
    }
    with TestClient(app_module.app) as client:
        response = client.post(
            "/repos/fix-ci", json=payload, headers={"x-forwarded-for": "203.0.113.42"}
        )

    assert response.status_code == 200
    keys = list(app_module._rate_limit_buckets.keys())
    assert any(key[0] == "testclient" for key in keys)
    assert all(key[0] != "203.0.113.42" for key in keys)


def test_rate_limit_uses_forwarded_for_when_proxy_trust_enabled(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_module, "RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(app_module, "RATE_LIMIT_REQUESTS_PER_WINDOW", 5)
    monkeypatch.setattr(app_module, "RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(app_module, "RATE_LIMIT_PATHS", {"/repos/fix-ci"})
    monkeypatch.setattr(app_module, "TRUST_PROXY_HEADERS", True)
    app_module._rate_limit_buckets.clear()

    monkeypatch.setattr(app_module, "create_job", lambda *_args, **_kwargs: "job-3")
    monkeypatch.setattr(app_module, "enqueue", lambda _job: None)

    payload = {
        "repo": "adaptco/motorsport-engineering-agent",
        "branch": "main",
        "patch": "diff --git a b",
    }
    with TestClient(app_module.app) as client:
        response = client.post(
            "/repos/fix-ci", json=payload, headers={"x-forwarded-for": "203.0.113.77, 10.0.0.1"}
        )

    assert response.status_code == 200
    keys = list(app_module._rate_limit_buckets.keys())
    assert any(key[0] == "203.0.113.77" for key in keys)


def test_rate_limit_cleanup_evicts_stale_buckets(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(app_module, "RATE_LIMIT_WINDOW_SECONDS", 1)
    monkeypatch.setattr(app_module, "RATE_LIMIT_REQUESTS_PER_WINDOW", 5)
    monkeypatch.setattr(app_module, "RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS", 1)
    monkeypatch.setattr(app_module, "RATE_LIMIT_PATHS", {"/repos/fix-ci"})
    monkeypatch.setattr(app_module, "TRUST_PROXY_HEADERS", False)
    app_module._rate_limit_buckets.clear()
    app_module._last_rate_limit_cleanup_at = 0.0

    old = time.monotonic() - 120.0
    app_module._rate_limit_buckets[("198.51.100.10", "/repos/fix-ci")] = deque([old])

    monkeypatch.setattr(app_module, "create_job", lambda *_args, **_kwargs: "job-4")
    monkeypatch.setattr(app_module, "enqueue", lambda _job: None)

    payload = {
        "repo": "adaptco/motorsport-engineering-agent",
        "branch": "main",
        "patch": "diff --git a b",
    }
    with TestClient(app_module.app) as client:
        response = client.post("/repos/fix-ci", json=payload)

    assert response.status_code == 200
    assert ("198.51.100.10", "/repos/fix-ci") not in app_module._rate_limit_buckets
