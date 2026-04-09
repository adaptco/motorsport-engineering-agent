"""control_plane/routes/aero module."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from control_plane.services.aero_state_store import append_aero_branch, build_initial_state, list_aero_states, load_aero_state, save_aero_state
from shared.models import AeroSimulationBranchRequest, AeroSimulationRunRequest, AeroSimulationStateRecord, AeroSimulationStateSummary

router = APIRouter(prefix="/aero", tags=["aero"])


@router.get("/runs", response_model=list[AeroSimulationStateSummary])
def list_aero_runs():
    return list_aero_states()


@router.post("/runs", response_model=AeroSimulationStateRecord, status_code=201)
def create_aero_run(req: AeroSimulationRunRequest):
    state = build_initial_state(req)
    return save_aero_state(state)


@router.get("/runs/{run_id}", response_model=AeroSimulationStateRecord)
def get_aero_run(run_id: str):
    state = load_aero_state(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="aero_run_not_found")
    return state


@router.post("/runs/{run_id}/branches", response_model=AeroSimulationStateRecord)
def propose_aero_branch(run_id: str, req: AeroSimulationBranchRequest):
    state = append_aero_branch(run_id, req)
    if state is None:
        raise HTTPException(status_code=404, detail="aero_run_not_found")
    return state
