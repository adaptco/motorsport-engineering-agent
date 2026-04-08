from __future__ import annotations

import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from control_plane.services.aero_runner import AeroSandboxRunner, WslOpenFoamRunner
from control_plane.services.aero_state_store import apply_aero_solver_result, build_initial_state, save_aero_state
from tests.fixtures import build_gt4_aero_run_request


def _wsl_integration_enabled() -> bool:
    return bool(os.environ.get("MEA_RUN_WSL_OPENFOAM_INTEGRATION")) and shutil.which("wsl.exe") is not None


def test_sandbox_runner_returns_deterministic_gt4_baseline(tmp_path: Path) -> None:
    req = build_gt4_aero_run_request()
    case_dir = tmp_path / "sandbox_case"

    result = AeroSandboxRunner().run(req, run_id="gt4-sandbox", case_dir=case_dir)

    assert result.execution_state.runner_kind == "sandbox"
    assert result.execution_state.environment == "sandbox"
    assert result.execution_state.status == "complete"
    assert result.execution_state.solver_status == "solved"
    assert result.cl == pytest.approx(-1.74)
    assert result.cd == pytest.approx(0.86)
    assert result.cm_pitch == pytest.approx(-0.045)
    assert (case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat").exists()
    assert (case_dir / "results" / "aero_result.json").exists()
    assert any(artifact.label == "force_coeffs" for artifact in result.artifacts)


def test_sandbox_result_updates_aero_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    req = build_gt4_aero_run_request()
    state = save_aero_state(build_initial_state(req))
    case_dir = tmp_path / "aero_state" / "cases" / state.simulation_run_id

    result = AeroSandboxRunner().run(req, run_id=state.simulation_run_id, case_dir=case_dir)
    updated = apply_aero_solver_result(state.simulation_run_id, result)

    assert updated is not None
    assert updated.lifecycle_state == "calibrating"
    assert updated.metric_snapshot["cl"] == result.cl
    assert updated.metric_snapshot["cd"] == result.cd
    assert updated.solver_state["case_status"] == "solved"
    assert updated.solver_state["execution_state"]["status"] == "complete"
    assert updated.calibration_state["status"] == "calibrating"


def test_wsl_runner_bootstrap_and_launch_command_scaffold(tmp_path: Path) -> None:
    runner = WslOpenFoamRunner()
    bootstrap = runner.bootstrap_script()
    command = runner.launch_command(tmp_path / "case")

    assert runner.profile.openfoam_package in bootstrap
    assert runner.profile.openfoam_bashrc in bootstrap
    assert "command -v blockMesh" in bootstrap
    assert command[0] == runner.profile.wsl_binary
    assert runner.profile.distro_name in command
    assert "blockMesh" in " ".join(command)
    assert "checkMesh" in " ".join(command)
    assert "simpleFoam" in " ".join(command)


def test_wsl_runner_parses_force_coeffs_and_updates_result(tmp_path: Path, monkeypatch) -> None:
    req = build_gt4_aero_run_request(runtime_target="wsl2", runner_kind="wsl")
    case_dir = tmp_path / "wsl_case"
    coeffs_path = case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat"
    coeffs_path.parent.mkdir(parents=True, exist_ok=True)
    coeffs_path.write_text(
        "\n".join(
            [
                "# Time Cd Cl CmRoll CmPitch CmYaw",
                "0.0 0.92 -1.58 0.000000 -0.030000 0.000000",
                "1.0 0.91 -1.57 0.000000 -0.028000 0.000000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    fake_completed = SimpleNamespace(returncode=0, stdout="blockMesh\ncheckMesh\nsimpleFoam\n", stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    result = WslOpenFoamRunner().run(req, case_dir=case_dir)

    assert result.execution_state.runner_kind == "wsl"
    assert result.execution_state.environment == "wsl2"
    assert result.execution_state.status == "complete"
    assert result.cl == pytest.approx(-1.57)
    assert result.cd == pytest.approx(0.91)
    assert result.cm_pitch == pytest.approx(-0.028)
    assert any(artifact.label == "force_coeffs" for artifact in result.artifacts)
    assert (case_dir / "results" / "aero_result.json").exists()


@pytest.mark.skipif(not _wsl_integration_enabled(), reason="WSL/OpenFOAM integration is gated by MEA_RUN_WSL_OPENFOAM_INTEGRATION and wsl.exe availability")
def test_wsl_integration_run_writes_back_to_aero_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))

    req = build_gt4_aero_run_request(runtime_target="wsl2", runner_kind="wsl")
    state = save_aero_state(build_initial_state(req))
    case_dir = tmp_path / "aero_state" / "cases" / state.simulation_run_id

    result = WslOpenFoamRunner().run(req, case_dir=case_dir)
    updated = apply_aero_solver_result(state.simulation_run_id, result)

    assert updated is not None
    assert updated.solver_state["execution_state"]["status"] in {"complete", "failed"}
    if result.execution_state.status == "complete":
        assert updated.lifecycle_state == "calibrating"
        assert updated.metric_snapshot["cl"] == result.cl
