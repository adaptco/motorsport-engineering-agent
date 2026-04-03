from mea.reasoning.policy_engine import PolicyEngine
from shared.models import Recommendation


def _rec(created_at_ns: int, rec_id: str = 'r1', priority: str = 'ADVISORY') -> Recommendation:
    return Recommendation(
        recommendation_id=rec_id,
        evidence_packet_id='ep-1',
        priority=priority,
        created_at_ns=created_at_ns,
    )


def test_logical_now_advances_on_submit():
    engine = PolicyEngine(ttl_ns=10_000_000_000)
    assert getattr(engine, '_logical_now_ns', 0) == 0

    r1 = _rec(1_000_000)
    engine.submit(r1)
    assert engine._logical_now_ns >= 1_000_000

    r2 = _rec(2_000_000, rec_id='r2')
    engine.submit(r2)
    assert engine._logical_now_ns >= 2_000_000


def test_decide_prefers_critical_over_advisory():
    engine = PolicyEngine(ttl_ns=10_000_000_000, cooldown_ns=0)
    engine.submit(_rec(1_000_000, rec_id='advisory', priority='ADVISORY'))
    engine.submit(_rec(2_000_000, rec_id='critical', priority='CRITICAL'))
    winner = engine.decide()
    assert winner is not None
    assert winner.recommendation_id == 'critical'
