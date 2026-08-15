"""control_plane/queue module."""

from __future__ import annotations

import json
import os
from collections import deque
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]

from shared.circuit_breaker import CircuitBreaker

QUEUE_NAME = "mea.jobs"
APP_ENV = os.environ.get("APP_ENV", "development").strip().lower()
_fallback_default = "true" if not os.environ.get("REDIS_URL") else ("false" if APP_ENV in {"prod", "production"} else "true")
QUEUE_ALLOW_IN_MEMORY_FALLBACK = os.environ.get(
    "QUEUE_ALLOW_IN_MEMORY_FALLBACK", _fallback_default
).strip().lower() in {
    "1",
    "true",
    "yes",
}
_memory_queue: deque[str] = deque()
_redis_breaker = CircuitBreaker.from_env("REDIS")
r: Any = None

if redis is not None:
    try:
        r = redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
        )
        r.ping()
    except Exception:  # pragma: no cover
        r = None
else:  # pragma: no cover
    r = None


def _fail_closed_or_fallback(payload: str | None = None):
    if not QUEUE_ALLOW_IN_MEMORY_FALLBACK:
        raise RuntimeError("redis_unavailable_and_memory_fallback_disabled")
    if payload is not None:
        _memory_queue.append(payload)
    return None


def enqueue(job: dict):
    payload = json.dumps(job)
    if r is None:
        _fail_closed_or_fallback(payload)
        return
    try:
        _redis_breaker.call(lambda: r.rpush(QUEUE_NAME, payload))
    except Exception:
        _fail_closed_or_fallback(payload)


def dequeue(timeout: int = 5):
    if r is not None:
        try:
            item = _redis_breaker.call(lambda: r.blpop(QUEUE_NAME, timeout=timeout))
        except Exception:
            if not QUEUE_ALLOW_IN_MEMORY_FALLBACK:
                raise
            item = None
        if item:
            return json.loads(item[1])
    if not _memory_queue:
        return None
    return json.loads(_memory_queue.popleft())
