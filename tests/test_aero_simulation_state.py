"""tests/test_aero_simulation_state module."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from control_plane.app import app
from tests.fixtures import build_gt4_aero_run_payload

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
