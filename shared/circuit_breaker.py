"""shared/circuit_breaker module."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import TypeVar

T = TypeVar("T")


class CircuitBreakerOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    state: str = field(default="closed", init=False)
    failure_count: int = field(default=0, init=False)
    opened_at: float | None = field(default=None, init=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    @classmethod
    def from_env(cls, name: str) -> CircuitBreaker:
        prefix = name.upper()
        threshold = int(os.environ.get(f"{prefix}_CB_FAILURE_THRESHOLD", "3"))
        timeout = float(os.environ.get(f"{prefix}_CB_RECOVERY_TIMEOUT_SECONDS", "30"))
        return cls(name=name, failure_threshold=max(threshold, 1), recovery_timeout_seconds=max(timeout, 1.0))

    def call(self, fn: Callable[..., T], *args, **kwargs) -> T:
        self._check_open_state()
        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise
        self._record_success()
        return result

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "name": self.name,
                "state": self.state,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout_seconds,
                "opened_at": self.opened_at,
            }

    def _check_open_state(self) -> None:
        with self._lock:
            if self.state != "open":
                return
            if self.opened_at is None:
                self.opened_at = time.monotonic()
            elapsed = time.monotonic() - self.opened_at
            if elapsed >= self.recovery_timeout_seconds:
                self.state = "half-open"
                return
            raise CircuitBreakerOpenError(
                f"{self.name}_circuit_open: retry after {self.recovery_timeout_seconds - elapsed:.1f}s"
            )

    def _record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                self.opened_at = time.monotonic()

    def _record_success(self) -> None:
        with self._lock:
            self.failure_count = 0
            self.state = "closed"
            self.opened_at = None
