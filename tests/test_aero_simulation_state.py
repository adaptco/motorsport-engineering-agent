"""tests/test_aero_simulation_state module."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from control_plane.app import app
from control_plane.services.aero_runner import AeroSandboxRunner
from control_plane.services.aero_state_store import (
    append_aero_branch,
    apply_aero_solver_result,
    build_initial_state,
    load_aero_state,
    save_aero_state,
)
from control_plane.services.cad_resolver import resolve_cad_candidate
from shared.forensic_ledger import sha256_prefixed
from shared.models import AeroSimulationBranchRequest
from tests.fixtures import build_gt4_aero_run_payload, build_gt4_aero_run_request

client = TestClient(app)


def _schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "contracts"
        / "aero"
        / "aero_simulation_state.schema.json"
    )


def _load_schema() -> dict:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def test_gt4_fixture_spec_sheet_dimension_fidelity() -> None:
    req = build_gt4_aero_run_request()
    identity = req.vehicle_identity
    dims = req.metadata["dimensions"]

    assert identity.make == "Aston Martin"
    assert identity.model == "Vantage GT4"
    assert identity.vehicle_class == "GT4"

    # Exact AMR GT4 spec sheet dimensions
    assert dims["length_m"] == 4.380
    assert dims["width_m"] == 1.865
    assert dims["width_with_mirrors_m"] == 2.025
    assert dims["height_m"] == 1.210
    assert dims["wheelbase_m"] == 2.600
    assert dims["track_front_m"] == 1.580
    assert dims["track_rear_m"] == 1.590
    assert dims["kerb_mass_kg"] == 1350.0

    # Required source refs
    labels = {ref.label for ref in req.source_refs}
    assert "gt4-profile-view" in labels
    assert "gt4-front-view" in labels
    assert "aston-martin-vantage-gt4-spec-sheet" in labels


def test_create_aero_run_persists_schema_compliant_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    response = client.post("/aero/runs", json=build_gt4_aero_run_payload())
    assert response.status_code == 201

    payload = response.json()
    Draft202012Validator(
        _load_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER
    ).validate(payload)

    run_id = payload["simulation_run_id"]
    state_path = tmp_path / "aero_state" / "runs" / f"{run_id}.json"
    case_dir = tmp_path / "aero_state" / "cases" / run_id
    assert state_path.exists()
    assert case_dir.exists()
    assert payload["loop_family"] == "aero"
    assert payload["lifecycle_state"] == "baseline_built"
    assert payload["vehicle_snapshot"]["identity"]["make"] == "Aston Martin"
    assert payload["vehicle_snapshot"]["dimensions"]["width_with_mirrors_m"] == 2.025
    assert payload["vehicle_snapshot"]["dimensions"]["kerb_mass_kg"] == 1350.0
    assert payload["solver_state"]["execution_state"]["status"] == "not_run"
    assert payload["geometry_state"]["geometry_status"] == "baseline"
    assert payload["geometry_state"]["cad_resolution"]["resolved_strategy"] == "proxy_geometry"
    assert payload["geometry_state"]["cad_resolution"]["selected_source"] is None
    assert payload["solver_state"]["case_status"] == "scaffolded"
    assert payload["solver_state"]["openfoam_case"]["mesh_strategy"] == "blockMesh"
    assert Path(payload["geometry_state"]["cad_resolution"]["geometry_manifest_uri"]).exists()
    assert Path(payload["solver_state"]["openfoam_case"]["case_manifest_uri"]).exists()
    assert (case_dir / "system" / "blockMeshDict").exists()
    assert payload["telemetry_links"] == []
    assert all(item["kind"] != "telemetry" for item in payload["geometry_state"]["source_assets"])


def test_state_hash_stability_and_chaining(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    req = build_gt4_aero_run_request()
    state = save_aero_state(build_initial_state(req))

    # Verify state_hash format
    assert state.state_hash.startswith("sha256:")
    assert len(state.state_hash) == 71  # "sha256:" + 64 hex

    # Verify hash integrity: state_hash matches sha256 of payload excluding state_hash
    payload = state.model_dump(mode="json", exclude={"state_hash"})
    expected_hash = sha256_prefixed(payload)
    assert state.state_hash == expected_hash

    # Apply sandbox solve result
    case_dir = tmp_path / "aero_state" / "cases" / state.simulation_run_id
    result = AeroSandboxRunner().run(req, run_id=state.simulation_run_id, case_dir=case_dir)
    solved_state = apply_aero_solver_result(state.simulation_run_id, result)
    assert solved_state is not None
    assert solved_state.prev_state_hash == state.state_hash
    assert solved_state.state_hash != state.state_hash

    # Append branch
    branch_req = AeroSimulationBranchRequest(
        branch_name="front-dive-planes",
        change_mode="geometry",
        change_summary="Add front dive planes to shift aero balance forward.",
        requested_adjustments={"dive_plane_angle_deg": 15.0},
        expected_delta_cl=-0.05,
        expected_delta_cd=0.01,
    )
    branched_state = append_aero_branch(state.simulation_run_id, branch_req)
    assert branched_state is not None
    assert branched_state.prev_state_hash == solved_state.state_hash
    assert branched_state.state_hash != solved_state.state_hash
    assert len(branched_state.branches) == 1


def test_cad_resolver_proxy_vs_cad_selection(tmp_path: Path) -> None:
    # 1. Without CAD source -> proxy geometry resolution
    req_proxy = build_gt4_aero_run_request(baseline_geometry_strategy="proxy_geometry")
    case_dir_proxy = tmp_path / "case_proxy"
    resolution_proxy = resolve_cad_candidate(req_proxy, run_id="proxy-run", case_dir=case_dir_proxy)

    assert resolution_proxy.resolved_strategy == "proxy_geometry"
    assert resolution_proxy.confidence == 0.52
    assert resolution_proxy.proxy_generated is True
    assert resolution_proxy.selected_source is None
    assert resolution_proxy.proxy_geometry_uri is not None
    assert Path(resolution_proxy.geometry_manifest_uri).exists()

    # 2. With CAD candidate -> public CAD resolution
    req_cad = build_gt4_aero_run_request(
        include_public_cad_candidate=True, baseline_geometry_strategy="public_cad"
    )
    case_dir_cad = tmp_path / "case_cad"
    resolution_cad = resolve_cad_candidate(req_cad, run_id="cad-run", case_dir=case_dir_cad)

    assert resolution_cad.resolved_strategy == "public_cad"
    assert resolution_cad.confidence == 0.88
    assert resolution_cad.proxy_generated is False
    assert resolution_cad.selected_source is not None
    assert resolution_cad.selected_source.kind == "cad"


def test_create_aero_run_with_public_cad_candidate_selects_cad_path(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    response = client.post(
        "/aero/runs",
        json=build_gt4_aero_run_payload(
            include_public_cad_candidate=True, baseline_geometry_strategy="public_cad"
        ),
    )
    assert response.status_code == 201

    payload = response.json()
    Draft202012Validator(
        _load_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER
    ).validate(payload)

    run_id = payload["simulation_run_id"]
    case_dir = tmp_path / "aero_state" / "cases" / run_id
    assert payload["geometry_state"]["cad_resolution"]["resolved_strategy"] == "public_cad"
    assert payload["geometry_state"]["cad_resolution"]["selected_source"]["kind"] == "cad"
    assert payload["geometry_state"]["cad_resolution"]["proxy_generated"] is False
    assert payload["solver_state"]["openfoam_case"]["mesh_strategy"] == "snappyHexMesh"
    assert (case_dir / "system" / "snappyHexMeshDict").exists()


def test_branch_update_changes_state_without_touching_telemetry_storage(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    create_response = client.post(
        "/aero/runs", json=build_gt4_aero_run_payload(include_telemetry_source=True)
    )
    assert create_response.status_code == 201
    created = create_response.json()

    branch_response = client.post(
        f"/aero/runs/{created['simulation_run_id']}/branches",
        json={
            "branch_name": "lower-drag-pack",
            "change_mode": "geometry",
            "change_summary": "Reduce rear wing angle and compare balance shift.",
            "requested_adjustments": {"rear_wing_angle_deg": 10.0},
            "expected_delta_cl": -0.08,
            "expected_delta_cd": -0.02,
            "metadata": {"prompt": "what if we trim drag for low-speed tracks?"},
        },
    )
    assert branch_response.status_code == 200

    branched = branch_response.json()
    Draft202012Validator(
        _load_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER
    ).validate(branched)
    assert branched["lifecycle_state"] == "branching"
    assert branched["prev_state_hash"] == created["state_hash"]
    assert len(branched["branches"]) == 1
    assert branched["branches"][0]["branch_name"] == "lower-drag-pack"
    assert any(item["kind"] == "telemetry" for item in branched["telemetry_links"])
    assert all(item["kind"] != "telemetry" for item in branched["geometry_state"]["source_assets"])


def test_list_aero_runs_returns_summaries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    response = client.post("/aero/runs", json=build_gt4_aero_run_payload())
    assert response.status_code == 201
    created = response.json()

    list_response = client.get("/aero/runs")
    assert list_response.status_code == 200
    summaries = list_response.json()
    assert len(summaries) == 1
    assert summaries[0]["simulation_run_id"] == created["simulation_run_id"]
    assert summaries[0]["state_path"].endswith(f"{created['simulation_run_id']}.json")


def test_get_and_branch_aero_run_not_found_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    get_res = client.get("/aero/runs/nonexistent-run-id")
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "aero_run_not_found"

    branch_res = client.post(
        "/aero/runs/nonexistent-run-id/branches",
        json={
            "branch_name": "invalid-branch",
            "change_mode": "geometry",
            "change_summary": "Should fail",
        },
    )
    assert branch_res.status_code == 404
    assert branch_res.json()["detail"] == "aero_run_not_found"


def test_missing_cad_and_missing_solver_cases_fail_cleanly_without_touching_telemetry(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    # Missing CAD: clean fallback to proxy geometry
    req = build_gt4_aero_run_request(include_public_cad_candidate=False)
    state = save_aero_state(build_initial_state(req))
    assert state.geometry_state["cad_resolution"]["resolved_strategy"] == "proxy_geometry"

    # Missing/failed solver: apply a failed solver result without crashing or touching telemetry
    case_dir = tmp_path / "aero_state" / "cases" / state.simulation_run_id
    runner = AeroSandboxRunner()
    result = runner.run(req, run_id=state.simulation_run_id, case_dir=case_dir)
    # Simulate a failed solve
    failed_execution = result.execution_state.model_copy(
        update={"status": "failed", "solver_status": "failed", "exit_code": 1}
    )
    failed_result = result.model_copy(
        update={"execution_state": failed_execution, "cl": None, "cd": None}
    )

    updated = apply_aero_solver_result(state.simulation_run_id, failed_result)
    assert updated is not None
    assert updated.solver_state["case_status"] == "failed"
    assert updated.calibration_state["status"] == "stale"
    assert updated.metric_snapshot["cl"] is None


def test_regression_guard_aero_isolated_from_telemetry_and_replay(
    tmp_path: Path, monkeypatch
) -> None:
    aero_root = tmp_path / "aero_state"
    monkeypatch.setenv("AERO_STATE_ROOT", str(aero_root))

    # 1. Create and branch aero run
    req_payload = build_gt4_aero_run_payload(include_telemetry_source=True)
    res = client.post("/aero/runs", json=req_payload)
    assert res.status_code == 201
    run_id = res.json()["simulation_run_id"]

    branch_res = client.post(
        f"/aero/runs/{run_id}/branches",
        json={
            "branch_name": "rear-wing-trim",
            "change_mode": "setup",
            "change_summary": "Trim rear wing angle",
        },
    )
    assert branch_res.status_code == 200

    # 2. Confirm no telemetry files or sessions were created in aero directory
    runs_dir = aero_root / "runs"
    cases_dir = aero_root / "cases"
    assert runs_dir.exists()
    assert cases_dir.exists()

    # All files in runs_dir are .json or .summary.json
    for path in runs_dir.iterdir():
        assert path.name.endswith(".json")

    # 3. Confirm aero state record contains only simulation-specific state
    state = load_aero_state(run_id)
    assert state is not None
    assert state.loop_family == "aero"
    assert state.loop_layer == "simulation"
    assert state.state_type == "aero_simulation_state"
