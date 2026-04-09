"""control_plane/routes/agent module."""

from __future__ import annotations

import os

from fastapi import APIRouter

from control_plane.services.supervisor_service import queue_agent_decision
from shared.forensic_ledger import append_receipt
from shared.models import AgentDecisionRequest, AgentDecisionResponse
from shared.runtime_paths import default_session_ledger_path

router = APIRouter(tags=['agent'])
LEDGER_DB_PATH = os.environ.get("SESSION_LEDGER_DB_PATH", str(default_session_ledger_path()))


@router.post('/agent/decision', response_model=AgentDecisionResponse)
def agent_decision(req: AgentDecisionRequest):
    append_receipt(
        LEDGER_DB_PATH,
        session_id=req.session_id,
        run_id=req.run_id,
        trace_id=req.trace_id,
        receipt_type='agent_decision_intent',
        status='ACCEPTED',
        job_name='supervisor_decision',
        principal_id=req.principal_id,
        authz_scope=req.authz_scope,
        policy_version=req.policy_version,
        cmd_vector=req.model_dump(mode='json'),
        payload={'phase': 'intent', 'provider': req.provider, 'model': req.model},
    )
    result = queue_agent_decision(req)
    append_receipt(
        LEDGER_DB_PATH,
        session_id=req.session_id,
        run_id=req.run_id,
        trace_id=req.trace_id,
        receipt_type='agent_decision_result',
        status='ACCEPTED',
        job_name='supervisor_decision',
        principal_id=req.principal_id,
        authz_scope=req.authz_scope,
        policy_version=req.policy_version,
        cmd_vector=req.model_dump(mode='json'),
        payload=result.model_dump(mode='json'),
    )
    return result
