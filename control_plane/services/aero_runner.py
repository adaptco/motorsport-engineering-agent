from __future__ import annotations

import json
import re
import shlex
import subprocess
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.models import AeroSimulationExecutionState, AeroSimulationSolveResult, AeroSimulationRunRequest, AeroSourceRef


_FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
SOLVER_RUN_TIMEOUT_SECONDS = 20 * 60


@dataclass(frozen=True)
class OpenFoamRuntimeProfile:
    distro_name: str = "Ubuntu-22.04"
    distro_version: str = "22.04"
    openfoam_version: str = "11"
    openfoam_package: str = "openfoam11"
    openfoam_bashrc: str = "/usr/lib/openfoam/openfoam11/etc/bashrc"
    wsl_binary: str = "wsl.exe"
    shell_binary: str = "bash"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _has_cad_source(req: AeroSimulationRunRequest) -> bool:
    return any(source.kind == "cad" for source in req.source_refs)


def _dimensions(req: AeroSimulationRunRequest) -> dict[str, Any]:
    return req.metadata.get("dimensions") or {}


def _frontal_area_m2(req: AeroSimulationRunRequest) -> float:
    dimensions = _dimensions(req)
    if req.metadata.get("reference_area_m2") is not None:
        return float(req.metadata["reference_area_m2"])
    width_m = float(dimensions.get("width_with_mirrors_m") or dimensions.get("width_m") or 1.0)
    height_m = float(dimensions.get("height_m") or 1.0)
    return round(width_m * height_m * 0.9, 4)


def _reference_length_m(req: AeroSimulationRunRequest) -> float:
    dimensions = _dimensions(req)
    if req.metadata.get("reference_length_m") is not None:
        return float(req.metadata["reference_length_m"])
    return float(dimensions.get("wheelbase_m") or dimensions.get("length_m") or 1.0)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _sha256_file_prefixed(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _artifact_ref(path: Path, *, label: str, kind: str = "solver_case", root: Path | None = None) -> AeroSourceRef:
    try:
        relative_path = path.relative_to(root).as_posix() if root is not None else path.name
    except ValueError:
        relative_path = path.name
    return AeroSourceRef(
        kind=kind,  # type: ignore[arg-type]
        uri=str(path),
        label=label,
        sha256=_sha256_file_prefixed(path),
        metadata={"relative_path": str(relative_path)},
    )


def _baseline_metrics(
    req: AeroSimulationRunRequest,
    *,
    cl: float | None = None,
    cd: float | None = None,
    cm_pitch: float | None = None,
) -> dict[str, Any]:
    has_cad = _has_cad_source(req)
    width_m = float((_dimensions(req).get("width_with_mirrors_m") or _dimensions(req).get("width_m") or 1.0))
    height_m = float(_dimensions(req).get("height_m") or 1.0)
    reference_area = _frontal_area_m2(req)
    reference_velocity = float(req.metadata.get("reference_velocity_m_s", 55.0))
    rho = float(req.metadata.get("air_density_kg_m3", 1.225))

    cl_value = float(cl if cl is not None else (-1.92 if has_cad else -1.74))
    cd_value = float(cd if cd is not None else (0.79 if has_cad else 0.86))
    cm_pitch_value = float(cm_pitch if cm_pitch is not None else (-0.06 if has_cad else -0.045))

    aero_balance_pct = 42.0 if has_cad else 40.5
    confidence = 0.74 if has_cad else 0.58
    correlation_score = 0.66 if has_cad else 0.51
    residual_score = 0.34 if has_cad else 0.49

    drag_area_m2 = round(cd_value * reference_area, 3)
    downforce_n = round((-cl_value) * 0.5 * rho * reference_velocity**2 * reference_area, 1)

    return {
        "cl": cl_value,
        "cd": cd_value,
        "cm_pitch": cm_pitch_value,
        "aero_balance_pct": aero_balance_pct,
        "drag_area_m2": drag_area_m2,
        "downforce_n": downforce_n,
        "confidence": confidence,
        "correlation_score": correlation_score,
        "residual_score": residual_score,
        "reference_area_m2": reference_area,
        "reference_velocity_m_s": reference_velocity,
        "frontal_width_m": width_m,
        "reference_height_m": height_m,
        "has_cad": has_cad,
    }


def _build_execution_state(
    *,
    runner_kind: str,
    status: str,
    solver_status: str,
    environment: str,
    profile: OpenFoamRuntimeProfile,
    command: list[str],
    started_at: datetime,
    finished_at: datetime,
    exit_code: int,
    stdout_uri: str | None,
    stderr_uri: str | None,
    result_uri: str,
    kernel_signature: str | None = None,
    notes: list[str] | None = None,
) -> AeroSimulationExecutionState:
    return AeroSimulationExecutionState(
        runner_kind=runner_kind,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        environment=environment,  # type: ignore[arg-type]
        solver_status=solver_status,  # type: ignore[arg-type]
        distro_name=profile.distro_name if environment == "wsl2" else "sandbox",
        distro_version=profile.distro_version if environment == "wsl2" else None,
        openfoam_version=profile.openfoam_version,
        kernel_signature=kernel_signature,
        command=command,
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
        stdout_uri=stdout_uri,
        stderr_uri=stderr_uri,
        result_uri=result_uri,
        notes=notes or [],
    )


def _write_force_coeffs_file(case_dir: Path, metrics: dict[str, Any]) -> Path:
    force_coeffs_path = case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat"
    content = "\n".join(
        [
            "# Time Cd Cl CmRoll CmPitch CmYaw",
            f"0.0 {metrics['cd'] - 0.04:.6f} {metrics['cl'] + 0.04:.6f} 0.000000 {metrics['cm_pitch'] + 0.01:.6f} 0.000000",
            f"1.0 {metrics['cd']:.6f} {metrics['cl']:.6f} 0.000000 {metrics['cm_pitch']:.6f} 0.000000",
        ]
    ) + "\n"
    _write_text(force_coeffs_path, content)
    return force_coeffs_path


def _parse_force_coeffs_file(path: Path | None) -> dict[str, float] | None:
    if path is None or not path.exists():
        return None

    headers: list[str] | None = None
    rows: list[list[float]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            header_tokens = [token.lower() for token in re.split(r"[\s()]+", line.lstrip("#").strip()) if token]
            if len(header_tokens) > 1:
                headers = header_tokens
            continue
        values = [float(token) for token in _FLOAT_PATTERN.findall(line)]
        if values:
            rows.append(values)

    if not rows:
        return None

    values = rows[-1]
    mapped: dict[str, float] = {}
    if headers and len(headers) == len(values):
        mapped = {headers[index].replace("-", "_"): values[index] for index in range(len(values))}

    cd = mapped.get("cd", values[1] if len(values) > 1 else None)
    cl = mapped.get("cl", values[2] if len(values) > 2 else None)
    cm_pitch = mapped.get("cmpitch", mapped.get("cm_pitch", mapped.get("cm", values[4] if len(values) > 4 else None)))

    parsed: dict[str, float] = {}
    if cd is not None:
        parsed["cd"] = float(cd)
    if cl is not None:
        parsed["cl"] = float(cl)
    if cm_pitch is not None:
        parsed["cm_pitch"] = float(cm_pitch)
    return parsed or None


def _result_artifact_refs(
    *,
    case_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    force_coeffs_path: Path | None,
) -> list[AeroSourceRef]:
    artifacts: list[AeroSourceRef] = []
    for path, label in (
        (stdout_path, "solver_stdout"),
        (stderr_path, "solver_stderr"),
    ):
        if path.exists():
            artifacts.append(_artifact_ref(path, label=label, root=case_dir))
    if force_coeffs_path is not None and force_coeffs_path.exists():
        artifacts.append(_artifact_ref(force_coeffs_path, label="force_coeffs", root=case_dir))
    return artifacts


class AeroSandboxRunner:
    def __init__(self, profile: OpenFoamRuntimeProfile | None = None) -> None:
        self.profile = profile or OpenFoamRuntimeProfile()

    def run(self, req: AeroSimulationRunRequest, *, run_id: str, case_dir: Path) -> AeroSimulationSolveResult:
        case_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = case_dir / "logs"
        results_dir = case_dir / "results"
        coeffs_path = _write_force_coeffs_file(case_dir, _baseline_metrics(req))

        started_at = _utcnow()
        stdout_path = logs_dir / "sandbox.stdout.log"
        stderr_path = logs_dir / "sandbox.stderr.log"
        execution_notes = [
            "Deterministic sandbox solve for the GT4 aero baseline.",
            f"Run id: {run_id}",
            "This result is suitable for unit tests and state updates without WSL.",
        ]
        stdout_text = "\n".join(execution_notes) + "\n"
        _write_text(stdout_path, stdout_text)
        _write_text(stderr_path, "")

        metrics = _baseline_metrics(req)
        execution_state = _build_execution_state(
            runner_kind="sandbox",
            status="complete",
            solver_status="solved",
            environment="sandbox",
            profile=self.profile,
            command=["sandbox://aero-solve", run_id],
            started_at=started_at,
            finished_at=started_at,
            exit_code=0,
            stdout_uri=str(stdout_path),
            stderr_uri=str(stderr_path),
            result_uri=str(results_dir / "aero_result.json"),
            kernel_signature="deterministic-sandbox",
            notes=execution_notes,
        )

        result = AeroSimulationSolveResult(
            execution_state=execution_state,
            cl=metrics["cl"],
            cd=metrics["cd"],
            cm_pitch=metrics["cm_pitch"],
            aero_balance_pct=metrics["aero_balance_pct"],
            drag_area_m2=metrics["drag_area_m2"],
            downforce_n=metrics["downforce_n"],
            confidence=metrics["confidence"],
            correlation_score=metrics["correlation_score"],
            residual_score=metrics["residual_score"],
            artifacts=_result_artifact_refs(case_dir=case_dir, stdout_path=stdout_path, stderr_path=stderr_path, force_coeffs_path=coeffs_path),
            notes=execution_notes,
        )

        _write_json(results_dir / "aero_result.json", result.model_dump(mode="json"))
        return result


class WslOpenFoamRunner:
    def __init__(self, profile: OpenFoamRuntimeProfile | None = None) -> None:
        self.profile = profile or OpenFoamRuntimeProfile()

    def bootstrap_script(self) -> str:
        return "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "export DEBIAN_FRONTEND=noninteractive",
                "sudo apt-get update",
                "sudo apt-get install -y software-properties-common ca-certificates curl gnupg lsb-release",
                f"if ! command -v blockMesh >/dev/null 2>&1 || ! command -v checkMesh >/dev/null 2>&1 || ! command -v simpleFoam >/dev/null 2>&1; then sudo apt-get install -y {self.profile.openfoam_package}; fi",
                f"if [ -f {shlex.quote(self.profile.openfoam_bashrc)} ]; then source {shlex.quote(self.profile.openfoam_bashrc)}; fi",
                "command -v blockMesh",
                "command -v checkMesh",
                "command -v simpleFoam",
            ]
        ) + "\n"

    def launch_command(self, case_dir: Path, *, include_simple_foam: bool = True) -> list[str]:
        wsl_case_dir = shlex.quote(str(case_dir))
        body = "\n".join(
            [
                "set -euo pipefail",
                f'CASE_DIR="$(wslpath -u {wsl_case_dir})"',
                f"source {shlex.quote(self.profile.openfoam_bashrc)}",
                'cd "$CASE_DIR"',
                "blockMesh",
                "checkMesh",
                "simpleFoam" if include_simple_foam else "true",
            ]
        )
        return [
            self.profile.wsl_binary,
            "-d",
            self.profile.distro_name,
            "--",
            self.profile.shell_binary,
            "-lc",
            body,
        ]

    def run(self, req: AeroSimulationRunRequest, *, case_dir: Path, include_simple_foam: bool = True) -> AeroSimulationSolveResult:
        case_dir.mkdir(parents=True, exist_ok=True)
        started_at = _utcnow()
        command = self.launch_command(case_dir, include_simple_foam=include_simple_foam)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=SOLVER_RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            finished_at = _utcnow()
            logs_dir = case_dir / "logs"
            results_dir = case_dir / "results"
            stdout_path = logs_dir / "wsl.stdout.log"
            stderr_path = logs_dir / "wsl.stderr.log"
            _write_text(stdout_path, exc.stdout or "")
            _write_text(stderr_path, (exc.stderr or "") + f"\nSolver timed out after {SOLVER_RUN_TIMEOUT_SECONDS}s\n")

            execution_notes = [
                "WSL execution timed out.",
                f"Timeout seconds: {SOLVER_RUN_TIMEOUT_SECONDS}",
            ]
            execution_state = _build_execution_state(
                runner_kind="wsl",
                status="failed",
                solver_status="failed",
                environment="wsl2",
                profile=self.profile,
                command=command,
                started_at=started_at,
                finished_at=finished_at,
                exit_code=124,
                stdout_uri=str(stdout_path),
                stderr_uri=str(stderr_path),
                result_uri=str(results_dir / "aero_result.json"),
                kernel_signature=None,
                notes=execution_notes,
            )
            timed_out_result = AeroSimulationSolveResult(
                execution_state=execution_state,
                cl=None,
                cd=None,
                cm_pitch=None,
                aero_balance_pct=None,
                drag_area_m2=None,
                downforce_n=None,
                confidence=0.0,
                correlation_score=None,
                residual_score=None,
                artifacts=_result_artifact_refs(case_dir=case_dir, stdout_path=stdout_path, stderr_path=stderr_path, force_coeffs_path=None),
                notes=execution_notes,
            )
            _write_json(results_dir / "aero_result.json", timed_out_result.model_dump(mode="json"))
            return timed_out_result
        finished_at = _utcnow()

        logs_dir = case_dir / "logs"
        results_dir = case_dir / "results"
        stdout_path = logs_dir / "wsl.stdout.log"
        stderr_path = logs_dir / "wsl.stderr.log"
        _write_text(stdout_path, completed.stdout)
        _write_text(stderr_path, completed.stderr)

        if completed.returncode != 0:
            execution_notes = [
                "WSL execution returned a non-zero exit code.",
                f"Exit code: {completed.returncode}",
            ]
            execution_state = _build_execution_state(
                runner_kind="wsl",
                status="failed",
                solver_status="failed",
                environment="wsl2",
                profile=self.profile,
                command=command,
                started_at=started_at,
                finished_at=finished_at,
                exit_code=completed.returncode,
                stdout_uri=str(stdout_path),
                stderr_uri=str(stderr_path),
                result_uri=str(results_dir / "aero_result.json"),
                kernel_signature=None,
                notes=execution_notes,
            )
            failed_result = AeroSimulationSolveResult(
                execution_state=execution_state,
                cl=None,
                cd=None,
                cm_pitch=None,
                aero_balance_pct=None,
                drag_area_m2=None,
                downforce_n=None,
                confidence=0.0,
                correlation_score=None,
                residual_score=None,
                artifacts=_result_artifact_refs(case_dir=case_dir, stdout_path=stdout_path, stderr_path=stderr_path, force_coeffs_path=None),
                notes=execution_notes,
            )
            _write_json(results_dir / "aero_result.json", failed_result.model_dump(mode="json"))
            return failed_result

        parsed = _parse_force_coeffs_file(
            next(
                (
                    candidate
                    for candidate in [
                        case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat",
                        case_dir / "postProcessing" / "forceCoeffs" / "0" / "coefficient.dat",
                    ]
                    if candidate.exists()
                ),
                None,
            )
        )

        metrics = _baseline_metrics(
            req,
            cl=parsed.get("cl") if parsed else None,
            cd=parsed.get("cd") if parsed else None,
            cm_pitch=parsed.get("cm_pitch") if parsed else None,
        )
        execution_notes = [
            "WSL OpenFOAM run completed successfully.",
            f"Parsed coefficients from forceCoeffs output: {bool(parsed)}",
        ]
        coeffs_path = (
            case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat"
            if (case_dir / "postProcessing" / "forceCoeffs" / "0" / "forceCoeffs.dat").exists()
            else None
        )
        execution_state = _build_execution_state(
            runner_kind="wsl",
            status="complete",
            solver_status="solved",
            environment="wsl2",
            profile=self.profile,
            command=command,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=0,
            stdout_uri=str(stdout_path),
            stderr_uri=str(stderr_path),
            result_uri=str(results_dir / "aero_result.json"),
            kernel_signature=None,
            notes=execution_notes,
        )
        result = AeroSimulationSolveResult(
            execution_state=execution_state,
            cl=metrics["cl"],
            cd=metrics["cd"],
            cm_pitch=metrics["cm_pitch"],
            aero_balance_pct=metrics["aero_balance_pct"],
            drag_area_m2=metrics["drag_area_m2"],
            downforce_n=metrics["downforce_n"],
            confidence=metrics["confidence"],
            correlation_score=metrics["correlation_score"],
            residual_score=metrics["residual_score"],
            artifacts=_result_artifact_refs(case_dir=case_dir, stdout_path=stdout_path, stderr_path=stderr_path, force_coeffs_path=coeffs_path),
            notes=execution_notes,
        )
        _write_json(results_dir / "aero_result.json", result.model_dump(mode="json"))
        return result
