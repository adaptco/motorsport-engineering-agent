"""tests/test_forensic_ledger module."""

from pathlib import Path

from shared.forensic_ledger import append_receipt, get_session_head, init_ledger, verify_chain


def test_forensic_ledger_chains_and_tracks_operational_head(tmp_path: Path):
    db_path = tmp_path / 'ledger.db'
    init_ledger(db_path)

    first = append_receipt(
        db_path,
        session_id='session-1',
        run_id='run-1',
        trace_id='trace-1',
        receipt_type='intent',
        status='ACCEPTED',
        job_name='verify_dir_exists',
        principal_id='agent_01',
        authz_scope='read-only',
        policy_version='rbac.v1',
        cmd_vector={'job_name': 'verify_dir_exists', 'params': {'path': '/tmp'}},
        payload={'stdout': '/tmp'},
    )
    second = append_receipt(
        db_path,
        session_id='session-1',
        run_id='run-1',
        trace_id='trace-2',
        receipt_type='result',
        status='REJECTED',
        job_name='write_can_packet',
        principal_id='agent_01',
        authz_scope='read-only',
        policy_version='rbac.v1',
        cmd_vector={'job_name': 'write_can_packet', 'params': {'bus': 'can0'}},
        payload={'error': 'job_not_allowed'},
    )

    assert second.prev_hash == first.state_hash
    head = get_session_head(db_path, 'session-1')
    assert head is not None
    assert head['last_logical_clock'] == 2
    assert head['last_status'] == 'REJECTED'
    assert head['last_operational_state_hash'] == first.state_hash

    verdict = verify_chain(db_path, 'session-1')
    assert verdict['ok'] is True
    assert verdict['receipts'] == 2
