from __future__ import annotations

from enum import Enum
from typing import Any


class TimeDomain(str, Enum):
    DATA = "DATA"
    WALL = "WALL"


def infer_time_domain(timestamp_ns: int, *, logical_now_ns: int = 0) -> TimeDomain:
    """Heuristic split between simulator/logical time and wall-clock time.

    DATA: monotonic, dense, near the run's logical timeline.
    WALL: unix-ish or externally supplied timestamps.
    """
    if timestamp_ns <= 0:
        return TimeDomain.DATA
    # Unix nanoseconds for years after ~2001 are > 1e18. Sim/logical clocks in tests are much smaller.
    if timestamp_ns >= 1_000_000_000_000_000_000:
        return TimeDomain.WALL
    if logical_now_ns and timestamp_ns < logical_now_ns * 10:
        return TimeDomain.DATA
    return TimeDomain.DATA


def validate_time_domain_transition(previous: TimeDomain | None, current: TimeDomain) -> bool:
    if previous is None:
        return True
    if previous == current:
        return True
    # crossing from DATA to WALL inside a replay path is suspicious but allowed only by explicit promotion
    return False


def classify_timestamp_payload(payload: dict[str, Any], *, logical_now_ns: int = 0) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in payload.items():
        if isinstance(value, int) and key.endswith('_ns'):
            result[key] = infer_time_domain(value, logical_now_ns=logical_now_ns).value
    return result
