from __future__ import annotations

import json
import os
from collections import deque
from typing import Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from redis import Redis

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]

QUEUE_NAME = "mea.jobs"
_memory_queue: deque[str] = deque()

r: Redis | None = None

if redis is not None:
    try:
        r = cast("Redis", redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True))
        r.ping()
    except Exception:  # pragma: no cover
        r = None


def enqueue(job: dict[str, Any]) -> None:
    payload = json.dumps(job)
    if r is not None:
        r.rpush(QUEUE_NAME, payload)
    else:
        _memory_queue.append(payload)


def dequeue(timeout: int = 5) -> dict[str, Any] | None:
    if r is not None:
        item: Any = r.blpop(QUEUE_NAME, timeout=timeout)
        if not item:
            return None
        return cast(dict[str, Any], json.loads(item[1]))
    if not _memory_queue:
        return None
    return cast(dict[str, Any], json.loads(_memory_queue.popleft()))
