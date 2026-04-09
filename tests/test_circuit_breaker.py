"""tests/test_circuit_breaker module."""

from __future__ import annotations

import time

import pytest

from shared.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(name="unit_test", failure_threshold=2, recovery_timeout_seconds=60)

    def _boom() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        breaker.call(_boom)
    with pytest.raises(RuntimeError):
        breaker.call(_boom)
    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(lambda: "ok")

    snapshot = breaker.snapshot()
    assert snapshot["state"] == "open"
    assert snapshot["failure_count"] == 2


def test_circuit_breaker_recovery_allows_calls() -> None:
    breaker = CircuitBreaker(
        name="unit_test_recover", failure_threshold=1, recovery_timeout_seconds=1
    )

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    time.sleep(1.1)
    assert breaker.call(lambda: "healthy") == "healthy"
    assert breaker.snapshot()["state"] == "closed"
