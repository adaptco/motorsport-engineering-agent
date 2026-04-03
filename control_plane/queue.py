import json
import os
from collections import deque

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

QUEUE_NAME = "mea.jobs"
_memory_queue: deque[str] = deque()

if redis is not None:
    try:
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        r.ping()
    except Exception:  # pragma: no cover
        r = None
else:  # pragma: no cover
    r = None


def enqueue(job: dict):
    payload = json.dumps(job)
    if r is not None:
        r.rpush(QUEUE_NAME, payload)
    else:
        _memory_queue.append(payload)


def dequeue(timeout: int = 5):
    if r is not None:
        item = r.blpop(QUEUE_NAME, timeout=timeout)
        if not item:
            return None
        return json.loads(item[1])
    if not _memory_queue:
        return None
    return json.loads(_memory_queue.popleft())
