"""shared/forensic_ledger module."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ISO_8601_UTC = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass(frozen=True)
class LedgerAppendResult:
    receipt_id: int
    session_id: str
    logical_clock: int
    status: str
    state_hash: str
    prev_hash: str | None


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_prefixed(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;

CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    logical_clock INTEGER NOT NULL,
    receipt_type TEXT NOT NULL,
    status TEXT NOT NULL,
    prev_hash TEXT,
    state_hash TEXT NOT NULL,
    job_name TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    authz_scope TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    decision_basis_hash TEXT NOT NULL,
    cmd_vector TEXT NOT NULL,
    payload TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(session_id, logical_clock),
    UNIQUE(state_hash)
);

CREATE INDEX IF NOT EXISTS idx_receipts_session_clock ON receipts(session_id, logical_clock);
CREATE INDEX IF NOT EXISTS idx_receipts_trace ON receipts(trace_id);
CREATE INDEX IF NOT EXISTS idx_receipts_run ON receipts(run_id);
CREATE INDEX IF NOT EXISTS idx_receipts_principal ON receipts(principal_id);
CREATE INDEX IF NOT EXISTS idx_receipts_job ON receipts(job_name);

CREATE TABLE IF NOT EXISTS session_heads (
    session_id TEXT PRIMARY KEY,
    last_receipt_id INTEGER NOT NULL,
    last_logical_clock INTEGER NOT NULL,
    last_state_hash TEXT NOT NULL,
    last_status TEXT NOT NULL,
    last_operational_state_hash TEXT,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def ledger_connection(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_ledger(db_path: str | Path) -> None:
    with ledger_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def _utcnow() -> str:
    return datetime.now(UTC).strftime(ISO_8601_UTC)


def _build_decision_basis_hash(
    *,
    principal_id: str,
    authz_scope: str,
    policy_version: str,
    job_name: str,
    cmd_vector: dict[str, Any],
) -> str:
    return sha256_prefixed(
        {
            "principal_id": principal_id,
            "authz_scope": authz_scope,
            "policy_version": policy_version,
            "job_name": job_name,
            "cmd_vector": cmd_vector,
        }
    )


def _next_state_hash(
    *,
    session_id: str,
    logical_clock: int,
    prev_hash: str | None,
    receipt_type: str,
    status: str,
    job_name: str,
    principal_id: str,
    authz_scope: str,
    policy_version: str,
    cmd_vector: dict[str, Any],
    payload: dict[str, Any] | None,
) -> str:
    return sha256_prefixed(
        {
            "session_id": session_id,
            "logical_clock": logical_clock,
            "prev_hash": prev_hash,
            "receipt_type": receipt_type,
            "status": status,
            "job_name": job_name,
            "principal_id": principal_id,
            "authz_scope": authz_scope,
            "policy_version": policy_version,
            "cmd_vector": cmd_vector,
            "payload": payload or {},
        }
    )


def append_receipt(
    db_path: str | Path,
    *,
    session_id: str,
    run_id: str,
    trace_id: str,
    receipt_type: str,
    status: str,
    job_name: str,
    principal_id: str,
    authz_scope: str,
    policy_version: str,
    cmd_vector: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> LedgerAppendResult:
    init_ledger(db_path)
    created_at = _utcnow()
    with ledger_connection(db_path) as conn:
        head = conn.execute(
            "SELECT last_logical_clock, last_state_hash, last_operational_state_hash FROM session_heads WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        logical_clock = 1 if head is None else int(head["last_logical_clock"]) + 1
        prev_hash = None if head is None else str(head["last_state_hash"])
        decision_basis_hash = _build_decision_basis_hash(
            principal_id=principal_id,
            authz_scope=authz_scope,
            policy_version=policy_version,
            job_name=job_name,
            cmd_vector=cmd_vector,
        )
        state_hash = _next_state_hash(
            session_id=session_id,
            logical_clock=logical_clock,
            prev_hash=prev_hash,
            receipt_type=receipt_type,
            status=status,
            job_name=job_name,
            principal_id=principal_id,
            authz_scope=authz_scope,
            policy_version=policy_version,
            cmd_vector=cmd_vector,
            payload=payload,
        )
        cursor = conn.execute(
            """
            INSERT INTO receipts (
                session_id, run_id, trace_id, logical_clock, receipt_type, status,
                prev_hash, state_hash, job_name, principal_id, authz_scope,
                policy_version, decision_basis_hash, cmd_vector, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                run_id,
                trace_id,
                logical_clock,
                receipt_type,
                status,
                prev_hash,
                state_hash,
                job_name,
                principal_id,
                authz_scope,
                policy_version,
                decision_basis_hash,
                canonical_json(cmd_vector),
                canonical_json(payload or {}),
                created_at,
            ),
        )
        receipt_id = int(cursor.lastrowid)
        last_operational_state_hash = (
            state_hash
            if status == "ACCEPTED"
            else (None if head is None else head["last_operational_state_hash"])
        )
        conn.execute(
            """
            INSERT INTO session_heads (
                session_id, last_receipt_id, last_logical_clock, last_state_hash,
                last_status, last_operational_state_hash, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                last_receipt_id=excluded.last_receipt_id,
                last_logical_clock=excluded.last_logical_clock,
                last_state_hash=excluded.last_state_hash,
                last_status=excluded.last_status,
                last_operational_state_hash=excluded.last_operational_state_hash,
                updated_at=excluded.updated_at
            """,
            (
                session_id,
                receipt_id,
                logical_clock,
                state_hash,
                status,
                last_operational_state_hash,
                created_at,
            ),
        )
        return LedgerAppendResult(
            receipt_id=receipt_id,
            session_id=session_id,
            logical_clock=logical_clock,
            status=status,
            state_hash=state_hash,
            prev_hash=prev_hash,
        )


def get_session_head(db_path: str | Path, session_id: str) -> dict[str, Any] | None:
    init_ledger(db_path)
    with ledger_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM session_heads WHERE session_id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


def verify_chain(db_path: str | Path, session_id: str) -> dict[str, Any]:
    init_ledger(db_path)
    with ledger_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM receipts WHERE session_id = ? ORDER BY logical_clock ASC, id ASC",
            (session_id,),
        ).fetchall()
        prev_hash: str | None = None
        expected_clock = 1
        details: list[dict[str, Any]] = []
        for row in rows:
            valid = True
            reason = None
            if int(row["logical_clock"]) != expected_clock:
                valid = False
                reason = "logical_clock_gap"
            elif row["prev_hash"] != prev_hash:
                valid = False
                reason = "prev_hash_mismatch"
            else:
                payload = json.loads(row["payload"]) if row["payload"] else {}
                cmd_vector = json.loads(row["cmd_vector"])
                recomputed = _next_state_hash(
                    session_id=row["session_id"],
                    logical_clock=int(row["logical_clock"]),
                    prev_hash=row["prev_hash"],
                    receipt_type=row["receipt_type"],
                    status=row["status"],
                    job_name=row["job_name"],
                    principal_id=row["principal_id"],
                    authz_scope=row["authz_scope"],
                    policy_version=row["policy_version"],
                    cmd_vector=cmd_vector,
                    payload=payload,
                )
                if recomputed != row["state_hash"]:
                    valid = False
                    reason = "state_hash_mismatch"
            details.append(
                {
                    "logical_clock": int(row["logical_clock"]),
                    "valid": valid,
                    "state_hash": row["state_hash"],
                    "prev_hash": row["prev_hash"],
                    "receipt_type": row["receipt_type"],
                    "status": row["status"],
                    "job_name": row["job_name"],
                }
            )
            if not valid:
                return {
                    "ok": False,
                    "reason": reason,
                    "at": int(row["logical_clock"]),
                    "details": details,
                }
            prev_hash = row["state_hash"]
            expected_clock += 1
        return {"ok": True, "receipts": len(rows), "head": prev_hash, "details": details}


def list_receipts(
    db_path: str | Path,
    session_id: str,
    *,
    after_logical_clock: int = 0,
    receipt_type: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    init_ledger(db_path)
    query = "SELECT * FROM receipts WHERE session_id = ? AND logical_clock > ?"
    params: list[Any] = [session_id, after_logical_clock]
    if receipt_type:
        query += " AND receipt_type = ?"
        params.append(receipt_type)
    query += " ORDER BY logical_clock ASC, id ASC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with ledger_connection(db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]
