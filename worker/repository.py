"""worker/repository module."""

import json

from shared.db import get_conn


def set_job_phase(
    job_id: str,
    status: str,
    phase: str,
    payload: dict | None = None,
    error_message: str | None = None,
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs SET status=%s, phase=%s, result_payload=COALESCE(%s::jsonb, result_payload),
            error_message=%s, updated_at=NOW() WHERE job_id=%s
            """,
            (
                status,
                phase,
                json.dumps(payload) if payload is not None else None,
                error_message,
                job_id,
            ),
        )
        cur.execute(
            "INSERT INTO job_events (job_id, level, event_type, payload) VALUES (%s, %s, %s, %s::jsonb)",
            (
                job_id,
                "ERROR" if error_message else "INFO",
                f"job.{phase}",
                json.dumps(payload or {"error": error_message} if error_message else {}),
            ),
        )


def add_span(job_id: str, trace_id: str, span_name: str, status: str, attributes: dict):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO spans (trace_id, span_name, status, attributes) VALUES (%s, %s, %s, %s::jsonb)",
            (trace_id, span_name, status, json.dumps(attributes)),
        )


def get_job_identity(job_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT trace_id, repo_slug, base_branch FROM jobs WHERE job_id=%s", (job_id,))
        row = cur.fetchone()
        return (
            {"trace_id": str(row[0]), "repo_slug": row[1], "base_branch": row[2]} if row else None
        )


def complete_job(job_id: str, fix_branch: str, pr_url: str, result_payload: dict):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET status='succeeded', phase='complete', fix_branch=%s, github_pr_url=%s, result_payload=%s::jsonb, updated_at=NOW()
            WHERE job_id=%s
            """,
            (fix_branch, pr_url, json.dumps(result_payload), job_id),
        )
        cur.execute(
            "INSERT INTO receipts (job_id, outcome, lineage, state_delta, payload) VALUES (%s, 'success', %s::jsonb, %s::jsonb, %s::jsonb) ON CONFLICT (job_id) DO NOTHING",
            (
                job_id,
                json.dumps({"source": "backend_worker"}),
                json.dumps({"status": "complete"}),
                json.dumps(result_payload),
            ),
        )
