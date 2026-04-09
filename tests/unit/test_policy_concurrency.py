"""tests/unit/test_policy_concurrency module."""

from concurrent.futures import ThreadPoolExecutor

from mea.reasoning.policy_engine import PolicyEngine
from shared.models import Recommendation


def _submit(engine: PolicyEngine, idx: int) -> None:
    engine.submit(Recommendation(
        recommendation_id=f'r{idx}',
        evidence_packet_id='ep-1',
        priority='ADVISORY',
        created_at_ns=idx + 1,
    ))


def test_policy_engine_queue_depth_stays_bounded_under_concurrency():
    engine = PolicyEngine(ttl_ns=10_000_000_000, cooldown_ns=0)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: _submit(engine, i), range(64)))
    assert engine.queue_depth() <= 1
