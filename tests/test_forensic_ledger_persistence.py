from __future__ import annotations

from pathlib import Path

from control_plane.app import validate_session_ledger_startup_config
from shared.forensic_ledger import append_receipt, get_session_head, verify_chain


def test_validate_session_ledger_startup_config_creates_parent_and_db(tmp_path: Path) -> None:
    ledger_path = tmp_path / "workflow_state" / "session-ledger.db"
    resolved = validate_session_ledger_startup_config(ledger_db_path=ledger_path)
    assert Path(resolved).exists()
    assert ledger_path.exists()


def test_session_ledger_write_read_roundtrip(tmp_path: Path) -> None:
    ledger_path = tmp_path / "workflow_state" / "session-ledger.db"
    validate_session_ledger_startup_config(ledger_db_path=ledger_path)

    append_receipt(
        ledger_path,
        session_id="session-1",
        run_id="run-1",
        trace_id="trace-1",
        receipt_type="session_evidence",
        status="ACCEPTED",
        job_name="store_session_evidence",
        principal_id="system",
        authz_scope="session:write",
        policy_version="rbac.v1",
        cmd_vector={"evidence_packet_id": "packet-1"},
        payload={"ok": True},
    )

    head = get_session_head(ledger_path, "session-1")
    assert head is not None
    assert int(head["last_logical_clock"]) == 1

    verdict = verify_chain(ledger_path, "session-1")
    assert verdict["ok"] is True
    assert verdict["receipts"] == 1
