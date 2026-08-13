from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from control_plane.services.aero_runner import AeroSandboxRunner, OpenFoamRuntimeProfile, WslOpenFoamRunner
from control_plane.services.aero_state_store import (
    apply_aero_solver_result,
    build_initial_state,
    save_aero_state,
)
from tests.fixtures import build_gt4_aero_run_request


def _wsl_integration_enabled() -> bool:
    return (
        bool(os.environ.get("MEA_RUN_WSL_OPENFOAM_INTEGRATION"))
        and shutil.which("wsl.exe") is not None
    )


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


def test_sandbox_runner_smoke_returns_meshed_status(tmp_path: Path) -> None:
    req = build_gt4_aero_run_request()
    case_dir = tmp_path / "sandbox_smoke_case"

    result = AeroSandboxRunner().run_smoke(req, run_id="gt4-sandbox-smoke", case_dir=case_dir)

    assert result.execution_state.runner_kind == "sandbox"
    assert result.execution_state.status == "complete"
    assert result.execution_state.solver_status == "meshed"
    assert result.cl is None
    assert result.cd is None
    assert (case_dir / "logs" / "sandbox.stdout.log").exists()
    assert (case_dir / "results" / "aero_result.json").exists()


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
    assert "command -v checkMesh" in bootstrap
    assert "command -v simpleFoam" in bootstrap
    assert command[0] == runner.profile.wsl_binary
    assert runner.profile.distro_name in command
    assert "blockMesh" in " ".join(command)
    assert "checkMesh" in " ".join(command)
    assert "simpleFoam" in " ".join(command)


def test_wsl_runner_is_wsl_available(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "/usr/bin/wsl.exe")
    assert runner.is_wsl_available() is True

    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: None)
    assert runner.is_wsl_available() is False


def test_wsl_runner_validate_distro_success(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "wsl.exe")
    mock_os_release = 'NAME="Ubuntu"\nVERSION="22.04.4 LTS (Jammy Jellyfish)"\nID=ubuntu\nVERSION_ID="22.04"\n---UNAME---\n5.15.153.1-microsoft-standard-WSL2\n'
    fake_completed = SimpleNamespace(returncode=0, stdout=mock_os_release, stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    status = runner.validate_distro()
    assert status["available"] is True
    assert status["valid"] is True
    assert status["distro_version"] == "22.04"
    assert "microsoft-standard-WSL2" in status["kernel"]
    assert status["error"] is None


def test_wsl_runner_validate_distro_failures(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: None)
    status_no_wsl = runner.validate_distro()
    assert status_no_wsl["available"] is False
    assert status_no_wsl["valid"] is False
    assert "not found" in status_no_wsl["error"]

    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "wsl.exe")
    fake_failed = SimpleNamespace(returncode=1, stdout="", stderr="Distro not found\n")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_failed)
    status_failed = runner.validate_distro()
    assert status_failed["available"] is False
    assert "Distro not found" in status_failed["error"]


def test_wsl_runner_validate_toolchain_success(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "wsl.exe")
    mock_output = "BASHRC:1\nBLOCKMESH:1\nCHECKMESH:1\nSIMPLEFOAM:1\nOF_VERSION:11\n"
    fake_completed = SimpleNamespace(returncode=0, stdout=mock_output, stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    status = runner.validate_toolchain()
    assert status["valid"] is True
    assert status["blockMesh"] is True
    assert status["checkMesh"] is True
    assert status["simpleFoam"] is True
    assert status["bashrc_found"] is True
    assert status["error"] is None


def test_wsl_runner_validate_toolchain_missing_tools(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "wsl.exe")
    mock_output = "BASHRC:0\nBLOCKMESH:0\nCHECKMESH:0\nSIMPLEFOAM:0\nOF_VERSION:\n"
    fake_completed = SimpleNamespace(returncode=0, stdout=mock_output, stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    status = runner.validate_toolchain()
    assert status["valid"] is False
    assert status["blockMesh"] is False
    assert status["simpleFoam"] is False


def test_wsl_runner_provision_environment_success_and_failure(monkeypatch) -> None:
    runner = WslOpenFoamRunner()
    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: "wsl.exe")
    fake_completed = SimpleNamespace(returncode=0, stdout="OpenFOAM 11 installed\n", stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    provision_res = runner.provision_environment()
    assert provision_res["success"] is True
    assert provision_res["exit_code"] == 0

    monkeypatch.setattr("control_plane.services.aero_runner.shutil.which", lambda binary: None)
    provision_res_no_wsl = runner.provision_environment()
    assert provision_res_no_wsl["success"] is False
    assert provision_res_no_wsl["exit_code"] == -1


def test_wsl_runner_smoke_path_returns_meshed_status(tmp_path: Path, monkeypatch) -> None:
    req = build_gt4_aero_run_request(runtime_target="wsl2", runner_kind="wsl")
    case_dir = tmp_path / "wsl_smoke_case"

    fake_completed = SimpleNamespace(returncode=0, stdout="blockMesh completed\ncheckMesh: Mesh OK.\n", stderr="")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed)

    result = WslOpenFoamRunner().run_smoke(req, case_dir=case_dir)
    assert result.execution_state.runner_kind == "wsl"
    assert result.execution_state.environment == "wsl2"
    assert result.execution_state.status == "complete"
    assert result.execution_state.solver_status == "meshed"
    assert result.cl is None
    assert result.cd is None
    assert (case_dir / "logs" / "wsl.stdout.log").exists()
    assert (case_dir / "results" / "aero_result.json").exists()


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

    fake_completed = SimpleNamespace(
        returncode=0, stdout="blockMesh\ncheckMesh\nsimpleFoam\n", stderr=""
    )
    monkeypatch.setattr(
        "control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_completed
    )

    result = WslOpenFoamRunner().run(req, case_dir=case_dir)

    assert result.execution_state.runner_kind == "wsl"
    assert result.execution_state.environment == "wsl2"
    assert result.execution_state.status == "complete"
    assert result.cl == pytest.approx(-1.57)
    assert result.cd == pytest.approx(0.91)
    assert result.cm_pitch == pytest.approx(-0.028)
    assert any(artifact.label == "force_coeffs" for artifact in result.artifacts)
    assert (case_dir / "results" / "aero_result.json").exists()


def test_wsl_runner_nonzero_exit_code_returns_failed_result(tmp_path: Path, monkeypatch) -> None:
    req = build_gt4_aero_run_request(runtime_target="wsl2", runner_kind="wsl")
    case_dir = tmp_path / "wsl_fail_case"

    fake_failed = SimpleNamespace(returncode=2, stdout="blockMesh error\n", stderr="FOAM FATAL ERROR\n")
    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", lambda *args, **kwargs: fake_failed)

    result = WslOpenFoamRunner().run(req, case_dir=case_dir)
    assert result.execution_state.runner_kind == "wsl"
    assert result.execution_state.status == "failed"
    assert result.execution_state.solver_status == "failed"
    assert result.execution_state.exit_code == 2
    assert result.cl is None
    assert (case_dir / "logs" / "wsl.stderr.log").exists()
    assert (case_dir / "results" / "aero_result.json").exists()


def test_wsl_runner_timeout_writes_logs_and_returns_failed_result(
    tmp_path: Path, monkeypatch
) -> None:
    req = build_gt4_aero_run_request(runtime_target="wsl2", runner_kind="wsl")
    case_dir = tmp_path / "wsl_timeout_case"

    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["wsl.exe", "-d", "Ubuntu-22.04", "--", "bash", "-lc", "simpleFoam"],
            timeout=10,
            output="timeout-stdout",
            stderr="timeout-stderr",
        )

    monkeypatch.setattr("control_plane.services.aero_runner.subprocess.run", _raise_timeout)

    result = WslOpenFoamRunner().run(req, case_dir=case_dir)

    assert result.execution_state.runner_kind == "wsl"
    assert result.execution_state.status == "failed"
    assert result.execution_state.exit_code == 124
    stdout_text = (case_dir / "logs" / "wsl.stdout.log").read_text(encoding="utf-8")
    stderr_text = (case_dir / "logs" / "wsl.stderr.log").read_text(encoding="utf-8")
    assert "timeout-stdout" in stdout_text
    assert "timeout-stderr" in stderr_text
    assert "Solver timed out after" in stderr_text
    assert (case_dir / "results" / "aero_result.json").exists()


def test_apply_aero_solver_result_nonexistent_run_returns_none(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AERO_STATE_ROOT", str(tmp_path / "aero_state"))
    req = build_gt4_aero_run_request()
    case_dir = tmp_path / "dummy_case"
    result = AeroSandboxRunner().run(req, run_id="nonexistent-run", case_dir=case_dir)
    assert apply_aero_solver_result("nonexistent-run", result) is None


@pytest.mark.skipif(
    not _wsl_integration_enabled(),
    reason="WSL/OpenFOAM integration is gated by MEA_RUN_WSL_OPENFOAM_INTEGRATION and wsl.exe availability",
)
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
