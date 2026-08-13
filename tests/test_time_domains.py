from __future__ import annotations

from mea.reasoning.time_domains import (
    TimeDomain,
    classify_timestamp_payload,
    infer_time_domain,
    validate_time_domain_transition,
)


def test_infer_time_domain() -> None:
    # 1. Non-positive or zero -> DATA
    assert infer_time_domain(0) == TimeDomain.DATA
    assert infer_time_domain(-100) == TimeDomain.DATA

    # 2. Unix nanoseconds (>= 1e18) -> WALL
    assert infer_time_domain(1_700_000_000_000_000_000) == TimeDomain.WALL

    # 3. Logical/simulator clock -> DATA
    assert infer_time_domain(1_000_000, logical_now_ns=500_000) == TimeDomain.DATA
    assert infer_time_domain(50_000_000, logical_now_ns=10_000_000) == TimeDomain.DATA
    assert infer_time_domain(999_999_999) == TimeDomain.DATA


def test_validate_time_domain_transition() -> None:
    assert validate_time_domain_transition(None, TimeDomain.DATA) is True
    assert validate_time_domain_transition(None, TimeDomain.WALL) is True
    assert validate_time_domain_transition(TimeDomain.DATA, TimeDomain.DATA) is True
    assert validate_time_domain_transition(TimeDomain.WALL, TimeDomain.WALL) is True
    assert validate_time_domain_transition(TimeDomain.DATA, TimeDomain.WALL) is False
    assert validate_time_domain_transition(TimeDomain.WALL, TimeDomain.DATA) is False


def test_classify_timestamp_payload() -> None:
    payload = {
        "start_time_ns": 1_700_000_000_000_000_000,
        "tick_time_ns": 50_000,
        "other_field": 123,
        "string_field": "test",
    }
    classified = classify_timestamp_payload(payload)
    assert classified == {
        "start_time_ns": "WALL",
        "tick_time_ns": "DATA",
    }
