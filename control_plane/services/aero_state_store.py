from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from control_plane.services.cad_resolver import CadResolution, resolve_cad_candidate
from control_plane.services.openfoam_adapter import OpenFOAMScaffoldResult, scaffold_openfoam_case
from shared.forensic_ledger import sha256_prefixed
from shared.models import (
    AeroSimulationBranchRequest,
    AeroSimulationRunRequest,
    AeroSimulationSolveResult,
    AeroSimulationStateRecord,
    AeroSimulationStateSummary,
    AeroSourceRef,
)
from shared.runtime_paths import default_aero_state_root

RUNS_DIR_NAME = "runs"
CASES_DIR_NAME = "cases"
SUMMARY_SUFFIX = ".summary.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _state_root() -> Path:
    root = default_aero_state_root()
    (root / RUNS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    (root / CASES_DIR_NAME).mkdir(parents=True, exist_ok=True)
    return root


def _state_path(run_id: str) -> Path:
    return _state_root() / RUNS_DIR_NAME / f"{run_id}.json"


def _summary_path(run_id: str) -> Path:
    return _state_root() / RUNS_DIR_NAME / f"{run_id}{SUMMARY_SUFFIX}"


def _case_dir(run_id: str) -> Path:
    path = _state_root() / CASES_DIR_NAME / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache(maxsize=1)
def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "aero" / "aero_simulation_state.schema.json"


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)


def _validate_state_payload(payload: dict[str, Any]) -> None:
    _validator().validate(payload)


def _hash_state_payload(payload: dict[str, Any]) -> str:
    return sha256_prefixed(payload)


def _seal_state(state: AeroSimulationStateRecord) -> AeroSimulationStateRecord:
    return state.model_copy(update={"state_hash": _hash_state_payload(state.model_dump(mode="json", exclude={"state_hash"}))})


def _build_dimensions(metadata: dict[str, Any]) -> dict[str, Any]:
    dimensions = metadata.get("dimensions") or {}
    return {
        "length_m": dimensions.get("length_m"),
        "width_m": dimensions.get("width_m"),
        "width_with_mirrors_m": dimensions.get("width_with_mirrors_m"),
        "height_m": dimensions.get("height_m"),
        "wheelbase_m": dimensions.get("wheelbase_m"),
        "track_front_m": dimensions.get("track_front_m"),
        "track_rear_m": dimensions.get("track_rear_m"),
        "kerb_mass_kg": dimensions.get("kerb_mass_kg"),
    }


def _build_aero_targets(metadata: dict[str, Any]) -> dict[str, Any]:
    aero_targets = metadata.get("aero_targets") or {}
    return {
        "body_style": aero_targets.get("body_style"),
        "active_aero": aero_targets.get("active_aero"),
        "front_splitter": aero_targets.get("front_splitter"),
        "rear_wing": aero_targets.get("rear_wing"),
        "diffuser": aero_targets.get("diffuser"),
        "baseline_ride_height_m": aero_targets.get("baseline_ride_height_m"),
        "baseline_yaw_deg": aero_targets.get("baseline_yaw_deg"),
        "baseline_pitch_deg": aero_targets.get("baseline_pitch_deg"),
    }


def _build_vehicle_snapshot(req: AeroSimulationRunRequest, source_refs: list[dict[str, Any]], case_path: Path) -> dict[str, Any]:
    return {
        "identity": req.vehicle_identity.model_dump(mode="json"),
        "dimensions": _build_dimensions(req.metadata),
        "aero_targets": _build_aero_targets(req.metadata),
        "input_sources": source_refs,
        "snapshot_notes": req.metadata.get("snapshot_notes", []),
        "case_hint": str(case_path),
    }


def _build_geometry_state(
    req: AeroSimulationRunRequest,
    source_refs: list[dict[str, Any]],
    cad_resolution: CadResolution,
) -> dict[str, Any]:
    geometry_sources = [ref for ref in source_refs if ref["kind"] != "telemetry"]
    return {
        "baseline_strategy": req.baseline_geometry_strategy,
        "source_assets": geometry_sources,
        "cad_resolution": cad_resolution.to_state_dict(),
        "parametric_overrides": req.metadata.get("parametric_overrides", {}),
        "geometry_status": "baseline",
        "topology_notes": req.metadata.get("topology_notes", []),
    }


def _build_execution_state(req: AeroSimulationRunRequest, openfoam_case: OpenFOAMScaffoldResult) -> dict[str, Any]:
    runtime_target = str(req.metadata.get("runtime_target", "wsl2"))
    environment = "wsl2" if runtime_target == "wsl2" else "sandbox"
    return {
        "runner_kind": str(req.metadata.get("runner_kind", "sandbox")),
        "status": "not_run",
        "environment": environment,
        "solver_status": openfoam_case.scaffold_status,
        "distro_name": str(req.metadata.get("wsl_distro_name", "Ubuntu-22.04")),
        "distro_version": str(req.metadata.get("wsl_distro_version", "22.04")),
        "openfoam_version": str(req.metadata.get("openfoam_version", "11")),
        "kernel_signature": None,
        "command": [],
        "exit_code": None,
        "started_at": None,
        "finished_at": None,
        "stdout_uri": None,
        "stderr_uri": None,
        "result_uri": None,
        "notes": [
            "Baseline case scaffolded and ready for sandbox or WSL execution.",
        ],
    }


def _build_solver_state(
    req: AeroSimulationRunRequest,
    case_path: Path,
    openfoam_case: OpenFOAMScaffoldResult,
) -> dict[str, Any]:
    return {
        "solver_family": "openfoam",
        "runtime_target": openfoam_case.runtime_target,
        "case_status": openfoam_case.scaffold_status,
        "case_directory": str(case_path),
        "boundary_conditions": req.metadata.get("boundary_conditions", {}),
        "fluid_properties": {
            "air_density_kg_m3": req.metadata.get("air_density_kg_m3", 1.225),
            "dynamic_viscosity_pa_s": req.metadata.get("dynamic_viscosity_pa_s", 1.81e-05),
            "reference_velocity_m_s": req.metadata.get("reference_velocity_m_s"),
            "reference_pressure_pa": req.metadata.get("reference_pressure_pa", 101325.0),
            "reference_temperature_k": req.metadata.get("reference_temperature_k", 293.15),
        },
        "execution_state": _build_execution_state(req, openfoam_case),
        "openfoam_case": openfoam_case.to_state_dict(),
        "case_artifacts": [artifact.model_dump(mode="json") for artifact in openfoam_case.case_files],
        "solver_notes": req.metadata.get("solver_notes", []),
    }


def _build_metric_snapshot(req: AeroSimulationRunRequest) -> dict[str, Any]:
    return {
        "cl": None,
        "cd": None,
        "cm_pitch": None,
        "aero_balance_pct": None,
        "drag_area_m2": None,
        "downforce_n": None,
        "confidence": 0.0,
        "correlation_score": None,
        "residual_score": None,
        "target_summary": req.simulation_objective,
    }


def _build_calibration_state(source_refs: list[dict[str, Any]]) -> dict[str, Any]:
    reference_set_refs = [ref for ref in source_refs if ref["kind"] in {"public_reference", "wind_tunnel"}]
    return {
        "status": "uninitialized",
        "reference_set_refs": reference_set_refs,
        "fit_quality": None,
        "correlation_score": None,
        "last_calibrated_at": None,
    }


def _build_resume_state(run_id: str, state_path: Path) -> dict[str, Any]:
    return {
        "checkpoint_uri": str(state_path),
        "resume_token": str(uuid.uuid4()),
        "replayable": True,
        "case_checkpoint_uri": str(_case_dir(run_id)),
    }


def _state_summary(state: AeroSimulationStateRecord) -> AeroSimulationStateSummary:
    return AeroSimulationStateSummary(
        simulation_run_id=state.simulation_run_id,
        project_id=state.project_id,
        vehicle_program_id=state.vehicle_program_id,
        lifecycle_state=state.lifecycle_state,
        state_hash=state.state_hash,
        updated_at=state.updated_at,
        state_path=str(_state_path(state.simulation_run_id)),
    )


def _write_state_summary(state: AeroSimulationStateRecord) -> None:
    summary = _state_summary(state).model_dump(mode="json")
    _summary_path(state.simulation_run_id).write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )


def build_initial_state(req: AeroSimulationRunRequest) -> AeroSimulationStateRecord:
    run_id = str(uuid.uuid4())
    now = _utcnow()
    state_path = _state_path(run_id)
    case_path = _case_dir(run_id)
    source_ref_models = list(req.source_refs)
    source_refs = [ref.model_dump(mode="json") for ref in source_ref_models]
    telemetry_links = [ref for ref in source_ref_models if ref.kind == "telemetry"]
    cad_resolution = resolve_cad_candidate(req, run_id=run_id, case_dir=case_path)
    openfoam_case = scaffold_openfoam_case(req, run_id=run_id, case_dir=case_path, cad_resolution=cad_resolution)
    state = AeroSimulationStateRecord(
        simulation_run_id=run_id,
        project_id=req.project_id,
        vehicle_program_id=req.vehicle_program_id,
        created_at=now,
        updated_at=now,
        state_hash="pending",
        prev_state_hash=None,
        vehicle_snapshot=_build_vehicle_snapshot(req, source_refs, case_path),
        geometry_state=_build_geometry_state(req, source_refs, cad_resolution),
        solver_state=_build_solver_state(req, case_path, openfoam_case),
        metric_snapshot=_build_metric_snapshot(req),
        provenance=source_ref_models,
        branches=[],
        telemetry_links=telemetry_links,
        calibration_state=_build_calibration_state(source_refs),
        resume_state=_build_resume_state(run_id, state_path),
        lifecycle_state="baseline_built",
    )
    return _seal_state(state)


def _merge_case_artifacts(existing: list[dict[str, Any]], new_artifacts: list[AeroSourceRef]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_uris: set[str] = set()
    for artifact in existing:
        uri = str(artifact.get("uri"))
        if uri in seen_uris:
            continue
        merged.append(artifact)
        seen_uris.add(uri)
    for artifact in new_artifacts:
        artifact_dict = artifact.model_dump(mode="json")
        uri = artifact_dict["uri"]
        if uri in seen_uris:
            continue
        merged.append(artifact_dict)
        seen_uris.add(uri)
    return merged


def apply_aero_solver_result(run_id: str, result: AeroSimulationSolveResult) -> AeroSimulationStateRecord | None:
    state = load_aero_state(run_id)
    if state is None:
        return None

    now = _utcnow()
    execution_state = result.execution_state.model_dump(mode="json")
    solver_state = dict(state.solver_state)
    solver_state["case_status"] = execution_state["solver_status"]
    solver_state["execution_state"] = execution_state
    solver_state["case_artifacts"] = _merge_case_artifacts(solver_state.get("case_artifacts", []), result.artifacts)

    openfoam_case = dict(solver_state.get("openfoam_case", {}))
    openfoam_case["scaffold_status"] = execution_state["solver_status"]
    solver_state["openfoam_case"] = openfoam_case

    metric_snapshot = dict(state.metric_snapshot)
    metric_snapshot.update(
        {
            "cl": result.cl,
            "cd": result.cd,
            "cm_pitch": result.cm_pitch,
            "aero_balance_pct": result.aero_balance_pct,
            "drag_area_m2": result.drag_area_m2,
            "downforce_n": result.downforce_n,
            "confidence": result.confidence,
            "correlation_score": result.correlation_score,
            "residual_score": result.residual_score,
        }
    )

    calibration_state = dict(state.calibration_state)
    if execution_state["status"] == "complete":
        calibration_state["status"] = "calibrating"
        calibration_state["fit_quality"] = result.confidence
        calibration_state["correlation_score"] = result.correlation_score
        calibration_state["last_calibrated_at"] = execution_state["finished_at"]
        lifecycle_state = "calibrating"
    else:
        calibration_state["status"] = "stale"
        lifecycle_state = state.lifecycle_state

    updated_state = state.model_copy(
        update={
            "updated_at": now,
            "lifecycle_state": lifecycle_state,
            "solver_state": solver_state,
            "metric_snapshot": metric_snapshot,
            "calibration_state": calibration_state,
        }
    )
    updated_state = updated_state.model_copy(update={"prev_state_hash": state.state_hash})
    return save_aero_state(_seal_state(updated_state))


def save_aero_state(state: AeroSimulationStateRecord) -> AeroSimulationStateRecord:
    payload = state.model_dump(mode="json")
    _validate_state_payload(payload)
    path = _state_path(state.simulation_run_id)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    validated_state = AeroSimulationStateRecord.model_validate(payload)
    _write_state_summary(validated_state)
    return validated_state


def load_aero_state(run_id: str) -> AeroSimulationStateRecord | None:
    path = _state_path(run_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    _validate_state_payload(payload)
    return AeroSimulationStateRecord.model_validate(payload)


def list_aero_states() -> list[AeroSimulationStateSummary]:
    root = _state_root() / RUNS_DIR_NAME
    summaries: list[AeroSimulationStateSummary] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.name.endswith(SUMMARY_SUFFIX):
            continue
        summary_path = _summary_path(path.stem)
        if summary_path.exists():
            summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            summaries.append(AeroSimulationStateSummary.model_validate(summary_payload))
            continue

        payload = json.loads(path.read_text(encoding="utf-8"))
        _validate_state_payload(payload)
        state = AeroSimulationStateRecord.model_validate(payload)
        summaries.append(_state_summary(state))
    return summaries


def append_aero_branch(run_id: str, req: AeroSimulationBranchRequest) -> AeroSimulationStateRecord | None:
    state = load_aero_state(run_id)
    if state is None:
        return None

    now = _utcnow()
    branch = {
        "branch_id": str(uuid.uuid4()),
        "branch_name": req.branch_name,
        "change_mode": req.change_mode,
        "change_summary": req.change_summary,
        "requested_adjustments": req.requested_adjustments,
        "expected_delta_cl": req.expected_delta_cl,
        "expected_delta_cd": req.expected_delta_cd,
        "metadata": req.metadata,
        "status": "proposed",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    updated_state = state.model_copy(
        update={
            "branches": [*state.branches, branch],
            "updated_at": now,
            "prev_state_hash": state.state_hash,
            "lifecycle_state": "branching",
            "state_hash": "pending",
        }
    )
    updated_state = updated_state.model_copy(
        update={"state_hash": _hash_state_payload(updated_state.model_dump(mode="json", exclude={"state_hash"}))}
    )
    return save_aero_state(updated_state)
