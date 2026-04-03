from __future__ import annotations

import json
import os
import uuid
from typing import Any

from fastapi import HTTPException

from control_plane.services.session_receipts import build_state_surface
from shared.db import get_conn
from shared.forensic_ledger import append_receipt, get_session_head, verify_chain
from shared.models import SessionEvidenceRequest, SessionLedgerReplayResponse, SessionLedgerReplayResult

SESSION_LEDGER_DB_PATH = os.environ.get("SESSION_LEDGER_DB_PATH", "/tmp/mea-session-ledger.db")


def create_job(job_type: str, repo_slug: str, base_branch: str, payload: dict) -> str:
    with get_conn() as conn, conn.cursor() as cur:
        job_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        cur.execute(
            '''
            INSERT INTO jobs (job_id, job_type, repo_slug, base_branch, status, phase, request_payload, trace_id)
            VALUES (%s, %s, %s, %s, 'queued', 'accepted', %s::jsonb, %s)
            ''',
            (job_id, job_type, repo_slug, base_branch, json.dumps(payload), trace_id),
        )
        cur.execute(
            "INSERT INTO traces (trace_id, job_id, trace_name) VALUES (%s, %s, %s)",
            (trace_id, job_id, f"{job_type}:{repo_slug}"),
        )
        cur.execute(
            "INSERT INTO job_events (job_id, level, event_type, payload) VALUES (%s, 'INFO', 'job.accepted', %s::jsonb)",
            (job_id, json.dumps({"repo": repo_slug, "branch": base_branch})),
        )
        return job_id


def update_job_phase(job_id: str, status: str, phase: str, result_payload: dict | None = None, error_message: str | None = None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            UPDATE jobs
            SET status=%s, phase=%s, result_payload=COALESCE(%s::jsonb, result_payload), error_message=%s, updated_at=NOW()
            WHERE job_id=%s
            ''',
            (status, phase, json.dumps(result_payload) if result_payload is not None else None, error_message, job_id),
        )
        cur.execute(
            "INSERT INTO job_events (job_id, level, event_type, payload) VALUES (%s, %s, %s, %s::jsonb)",
            (
                job_id,
                "ERROR" if error_message else "INFO",
                f"job.{phase}",
                json.dumps(result_payload or {"error": error_message} if error_message else {}),
            ),
        )


def get_job(job_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT job_id, status, phase, github_pr_url, trace_id, result_payload FROM jobs WHERE job_id=%s", (job_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "job_id": str(row[0]),
            "status": row[1],
            "phase": row[2],
            "pr_url": row[3],
            "trace_id": str(row[4]) if row[4] else None,
            "summary": (row[5] or {}).get("summary") if row[5] else None,
        }


def list_trace(job_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT trace_id FROM jobs WHERE job_id=%s", (job_id,))
        row = cur.fetchone()
        if not row:
            return None
        trace_id = row[0]
        cur.execute("SELECT span_name, status, attributes FROM spans WHERE trace_id=%s ORDER BY started_at ASC", (trace_id,))
        spans = [{"span_name": r[0], "status": r[1], "attributes": r[2]} for r in cur.fetchall()]
        return {"job_id": job_id, "trace_id": str(trace_id), "spans": spans}


def store_webhook(delivery_id: str, event_name: str, repo_slug: str | None, payload: dict):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO webhook_events (delivery_id, event_name, repo_slug, payload)
            VALUES (%s, %s, %s, %s::jsonb)
            ON CONFLICT (delivery_id) DO NOTHING
            ''',
            (delivery_id, event_name, repo_slug, json.dumps(payload)),
        )


def correlate_workflow_run(repo_slug: str, run_id: str, payload: dict):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            UPDATE jobs
            SET github_run_id=%s, result_payload=COALESCE(result_payload, '{}'::jsonb) || %s::jsonb, updated_at=NOW()
            WHERE repo_slug=%s AND (github_run_id IS NULL OR github_run_id=%s)
            ''',
            (run_id, json.dumps({"workflow_run": payload.get("workflow_run", {})}), repo_slug, run_id),
        )


def _group_recommendations(req: SessionEvidenceRequest) -> dict[str, list]:
    grouped: dict[str, list] = {}
    packet_ids = {packet.evidence_packet_id for packet in req.evidence_packets}
    for rec in req.recommendations:
        if rec.evidence_packet_id not in packet_ids:
            raise HTTPException(status_code=400, detail=f"INVALID_EVIDENCE_LINK:{rec.evidence_packet_id}")
        grouped.setdefault(rec.evidence_packet_id, []).append(rec)
    return grouped


def _maybe_store_runtime_rows(req: SessionEvidenceRequest, grouped: dict[str, list]) -> None:
    try:
        with get_conn() as conn, conn.cursor() as cur:
            for packet in req.evidence_packets:
                cur.execute(
                    '''
                    INSERT INTO session_evidence (evidence_packet_id, session_id, timestamp_logical_ns, timestamp_wall, severity, features)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (evidence_packet_id) DO NOTHING
                    ''',
                    (
                        packet.evidence_packet_id,
                        packet.session_id,
                        packet.timestamp_logical_ns,
                        packet.timestamp_wall,
                        packet.severity,
                        json.dumps(packet.features.model_dump(mode="json")),
                    ),
                )
                for rec in grouped.get(packet.evidence_packet_id, []):
                    cur.execute(
                        '''
                        INSERT INTO recommendations_runtime (recommendation_id, evidence_packet_id, priority, trigger, action, expected_effect)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (recommendation_id) DO NOTHING
                        ''',
                        (
                            rec.recommendation_id,
                            rec.evidence_packet_id,
                            rec.priority,
                            rec.trigger,
                            rec.action,
                            rec.expected_effect,
                        ),
                    )
    except Exception:
        # Postgres persistence is optional during local kernel validation.
        return


def store_evidence_batch(req: SessionEvidenceRequest) -> dict[str, Any]:
    if not req.evidence_packets:
        raise HTTPException(status_code=400, detail="NO_EVIDENCE_PACKETS")
    for packet in req.evidence_packets:
        if packet.session_id != req.session_id:
            raise HTTPException(status_code=400, detail="SESSION_ID_MISMATCH")

    grouped = _group_recommendations(req)
    ordered_packets = sorted(req.evidence_packets, key=lambda p: p.timestamp_logical_ns)
    _maybe_store_runtime_rows(req, grouped)

    run_id = req.run_id or str(uuid.uuid4())
    head = get_session_head(SESSION_LEDGER_DB_PATH, req.session_id)
    latest_state_hash: str | None = head["last_state_hash"] if head else None
    receipts_created = 0

    for idx, packet in enumerate(ordered_packets, start=1):
        recommendations = grouped.get(packet.evidence_packet_id, [])
        state_surface = build_state_surface(packet, recommendations)
        result = append_receipt(
            SESSION_LEDGER_DB_PATH,
            session_id=req.session_id,
            run_id=run_id,
            trace_id=req.trace_id or f"evidence-{idx}",
            receipt_type="session_evidence",
            status="ACCEPTED",
            job_name="store_session_evidence",
            principal_id=req.principal_id,
            authz_scope=req.authz_scope,
            policy_version=req.policy_version,
            cmd_vector={
                "evidence_packet_id": packet.evidence_packet_id,
                "recommendation_ids": [r.recommendation_id for r in recommendations],
            },
            payload=state_surface,
        )
        latest_state_hash = result.state_hash
        receipts_created += 1

    return {
        "stored": len(req.evidence_packets) + len(req.recommendations),
        "receipts_created": receipts_created,
        "latest_state_hash": latest_state_hash,
    }


def replay_session_ledger(session_id: str) -> SessionLedgerReplayResponse:
    verdict = verify_chain(SESSION_LEDGER_DB_PATH, session_id)
    receipts = [
        SessionLedgerReplayResult(
            logical_clock=item["logical_clock"],
            valid=item["valid"],
            state_hash=item["state_hash"],
            prev_hash=item["prev_hash"],
            receipt_type=item["receipt_type"],
            status=item["status"],
            job_name=item["job_name"],
        )
        for item in verdict.get("details", [])
    ]
    return SessionLedgerReplayResponse(session_id=session_id, chain_ok=bool(verdict["ok"]), receipts=receipts)
