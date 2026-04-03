from fastapi import APIRouter

from control_plane.repository import replay_session_ledger, store_evidence_batch
from shared.models import SessionEvidenceRequest, SessionEvidenceResponse, SessionLedgerReplayResponse

router = APIRouter(tags=["session"])


@router.post("/session/evidence", response_model=SessionEvidenceResponse)
def ingest_evidence(req: SessionEvidenceRequest):
    result = store_evidence_batch(req)
    return SessionEvidenceResponse(status="ok", **result)


@router.get("/session/{session_id}/replay-ledger", response_model=SessionLedgerReplayResponse)
def replay_ledger(session_id: str):
    return replay_session_ledger(session_id)
