"""control_plane/routes/replay module."""


from fastapi import APIRouter

from control_plane.services.replay_service import replay_artifact
from shared.models import ReplayRequest, ReplayResponse

router = APIRouter(tags=["replay"])


@router.post("/session/replay", response_model=ReplayResponse)
def replay_session(req: ReplayRequest):
    return replay_artifact(req)
