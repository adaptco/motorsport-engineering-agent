from __future__ import annotations
import tempfile

import os

from fastapi import APIRouter, HTTPException

from control_plane.services.job_runner import JobExecutionRequest, JobNotAllowedError, execute_job
from shared.forensic_ledger import append_receipt

router = APIRouter(tags=["verifier"])
LEDGER_DB_PATH = os.environ.get("SESSION_LEDGER_DB_PATH", os.path.join(tempfile.gettempdir(), "mea-session-ledger.db"))


@router.post("/verifier/execute")
def verifier_execute(req: JobExecutionRequest):
    append_receipt(
        LEDGER_DB_PATH,
        session_id=req.session_id,
        run_id=req.run_id,
        trace_id=req.trace_id,
        receipt_type="verifier_intent",
        status="ACCEPTED",
        job_name=req.job_name,
        principal_id=req.principal_id,
        authz_scope=req.authz_scope,
        policy_version=req.policy_version,
        cmd_vector=req.model_dump(mode="json"),
        payload={"phase": "intent"},
    )
    try:
        result = execute_job(req)
        append_receipt(
            LEDGER_DB_PATH,
            session_id=req.session_id,
            run_id=req.run_id,
            trace_id=req.trace_id,
            receipt_type="verifier_result",
            status="ACCEPTED" if result.status == "complete" else "ERROR",
            job_name=req.job_name,
            principal_id=req.principal_id,
            authz_scope=req.authz_scope,
            policy_version=req.policy_version,
            cmd_vector=req.model_dump(mode="json"),
            payload=result.model_dump(mode="json"),
        )
        return result.model_dump()
    except JobNotAllowedError as exc:
        append_receipt(
            LEDGER_DB_PATH,
            session_id=req.session_id,
            run_id=req.run_id,
            trace_id=req.trace_id,
            receipt_type="verifier_result",
            status="REJECTED",
            job_name=req.job_name,
            principal_id=req.principal_id,
            authz_scope=req.authz_scope,
            policy_version=req.policy_version,
            cmd_vector=req.model_dump(mode="json"),
            payload={"error": str(exc)},
        )
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        append_receipt(
            LEDGER_DB_PATH,
            session_id=req.session_id,
            run_id=req.run_id,
            trace_id=req.trace_id,
            receipt_type="verifier_result",
            status="ERROR",
            job_name=req.job_name,
            principal_id=req.principal_id,
            authz_scope=req.authz_scope,
            policy_version=req.policy_version,
            cmd_vector=req.model_dump(mode="json"),
            payload={"error": str(exc)},
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
