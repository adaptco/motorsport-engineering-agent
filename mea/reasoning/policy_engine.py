"""mea/reasoning/policy_engine module."""

from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field

from shared.models import Recommendation

_PRIORITY = {"CRITICAL": 0, "WARNING": 1, "ADVISORY": 2, "INFO": 3, "NONE": 4}


@dataclass(order=True)
class _QueuedRecommendation:
    sort_key: tuple[int, int] = field(init=False, repr=False)
    priority_rank: int
    created_at_ns: int
    recommendation: Recommendation = field(compare=False)

    def __post_init__(self) -> None:
        self.sort_key = (self.priority_rank, self.created_at_ns)


class PolicyEngine:
    def __init__(self, ttl_ns: int = 2_000_000_000, cooldown_ns: int = 3_000_000_000) -> None:
        self.ttl_ns = ttl_ns
        self.cooldown_ns = cooldown_ns
        self._logical_now_ns = 0
        self._last_delivery_ns = 0
        self._queue: list[_QueuedRecommendation] = []
        self._lock = threading.RLock()

    def submit(self, rec: Recommendation) -> None:
        created_at_ns = self._extract_created_at_ns(rec)
        with self._lock:
            self._logical_now_ns = max(self._logical_now_ns, created_at_ns)
            self._drop_stale_locked()
            queued = _QueuedRecommendation(
                priority_rank=_PRIORITY.get(rec.priority, 99),
                created_at_ns=created_at_ns,
                recommendation=rec,
            )
            if len(self._queue) >= 1:
                current = self._queue[0]
                if queued.priority_rank < current.priority_rank:
                    heapq.heapreplace(self._queue, queued)
                elif (
                    queued.priority_rank == current.priority_rank
                    and queued.created_at_ns < current.created_at_ns
                ):
                    heapq.heapreplace(self._queue, queued)
                return
            heapq.heappush(self._queue, queued)

    def logical_now_ns(self) -> int:
        with self._lock:
            return self._now()

    def decide(self) -> Recommendation | None:
        with self._lock:
            self._drop_stale_locked()
            if not self._queue:
                return None
            now = self._now()
            candidate = self._queue[0]
            if (
                candidate.priority_rank > 0
                and self._last_delivery_ns
                and now - self._last_delivery_ns < self.cooldown_ns
            ):
                return None
            heapq.heappop(self._queue)
            self._last_delivery_ns = now
            return candidate.recommendation

    def queue_depth(self) -> int:
        with self._lock:
            self._drop_stale_locked()
            return len(self._queue)

    def _now(self) -> int:
        return self._logical_now_ns if self._logical_now_ns > 0 else time.monotonic_ns()

    def _extract_created_at_ns(self, rec: Recommendation) -> int:
        if hasattr(rec, "created_at_ns") and isinstance(rec.created_at_ns, int):
            return int(rec.created_at_ns)
        extra = getattr(rec, "metadata", None)
        if isinstance(extra, dict) and isinstance(extra.get("created_at_ns"), int):
            return int(extra["created_at_ns"])
        return self._now()

    def _drop_stale_locked(self) -> None:
        if not self._queue:
            return
        now = self._now()
        keep: list[_QueuedRecommendation] = []
        while self._queue:
            item = heapq.heappop(self._queue)
            if now - item.created_at_ns <= self.ttl_ns:
                keep.append(item)
        for item in keep:
            heapq.heappush(self._queue, item)
