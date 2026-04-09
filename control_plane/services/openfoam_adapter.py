"""control_plane/services/openfoam_adapter module."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from control_plane.services.cad_resolver import CadResolution
from shared.forensic_ledger import sha256_prefixed
from shared.models import AeroSimulationRunRequest, AeroSourceRef


def _safe_name(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip().lower())
    return normalized.strip("-") or "vehicle"


def _write_text_artifact(path: Path, content: str, *, label: str, kind: str = "solver_case") -> AeroSourceRef:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return AeroSourceRef(
        kind=kind,  # type: ignore[arg-type]
        uri=str(path),
        label=label,
        sha256=sha256_prefixed(content),
        metadata={"relative_path": str(path.name)},
    )


def _write_json_artifact(path: Path, payload: dict[str, Any], *, label: str, kind: str = "solver_case") -> AeroSourceRef:
    serialized = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return AeroSourceRef(
        kind=kind,  # type: ignore[arg-type]
        uri=str(path),
        label=label,
        sha256=sha256_prefixed(payload),
        metadata={"relative_path": str(path.name)},
    )


def _reference_area_m2(req: AeroSimulationRunRequest) -> float:
    dimensions = req.metadata.get("dimensions") or {}
    if req.metadata.get("reference_area_m2") is not None:
        return float(req.metadata["reference_area_m2"])
    width_m = dimensions.get("width_with_mirrors_m") or dimensions.get("width_m") or 1.0
    height_m = dimensions.get("height_m") or 1.0
    return round(float(width_m) * float(height_m) * 0.9, 4)


def _reference_length_m(req: AeroSimulationRunRequest) -> float:
    dimensions = req.metadata.get("dimensions") or {}
    if req.metadata.get("reference_length_m") is not None:
        return float(req.metadata["reference_length_m"])
    return float(dimensions.get("wheelbase_m") or dimensions.get("length_m") or 1.0)


def _build_control_dict(req: AeroSimulationRunRequest, runtime_target: str) -> str:
    rho_inf = req.metadata.get("air_density_kg_m3", 1.225)
    velocity = req.metadata.get("reference_velocity_m_s", 55.0)
    reference_area = _reference_area_m2(req)
    reference_length = _reference_length_m(req)
    return "\n".join(
        [
            "application     simpleFoam;",
            "startFrom       latestTime;",
            "startTime       0;",
            "stopAt          endTime;",
            "endTime         100;",
            "deltaT          1;",
            "writeControl    timeStep;",
            "writeInterval   10;",
            "purgeWrite      0;",
            "functions",
            "{",
            "    forceCoeffs",
            "    {",
            "        type            forceCoeffs;",
            '        libs            ("libforces.so");',
            '        patches         ("vehicle");',
            f"        rhoInf          {rho_inf};",
            f"        magUInf         {velocity};",
            "        liftDir         (0 0 1);",
            "        dragDir         (1 0 0);",
            "        pitchAxis       (0 1 0);",
            "        CofR            (0 0 0);",
            f"        Aref            {reference_area};",
            f"        lRef            {reference_length};",
            "        writeControl    timeStep;",
            "        writeInterval   1;",
            "    }",
            "}",
            f"// runtime_target: {runtime_target}",
        ]
    ) + "\n"


@dataclass(frozen=True)
class OpenFOAMScaffoldResult:
    case_name: str
    case_directory: str
    runtime_target: str
    requested_strategy: str
    resolved_strategy: str
    mesh_strategy: str
    scaffold_status: str
    solver_entrypoint: str
    cad_resolution_uri: str
    selected_geometry_uri: str
    case_manifest_uri: str
    case_manifest_sha256: str
    case_files: list[AeroSourceRef] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "case_directory": self.case_directory,
            "runtime_target": self.runtime_target,
            "requested_strategy": self.requested_strategy,
            "resolved_strategy": self.resolved_strategy,
            "mesh_strategy": self.mesh_strategy,
            "scaffold_status": self.scaffold_status,
            "solver_entrypoint": self.solver_entrypoint,
            "cad_resolution_uri": self.cad_resolution_uri,
            "selected_geometry_uri": self.selected_geometry_uri,
            "case_manifest_uri": self.case_manifest_uri,
            "case_manifest_sha256": self.case_manifest_sha256,
            "case_files": [artifact.model_dump(mode="json") for artifact in self.case_files],
            "notes": list(self.notes),
        }


def scaffold_openfoam_case(
    req: AeroSimulationRunRequest,
    *,
    run_id: str,
    case_dir: Path,
    cad_resolution: CadResolution,
) -> OpenFOAMScaffoldResult:
    system_dir = case_dir / "system"
    constant_dir = case_dir / "constant"
    zero_dir = case_dir / "0"
    logs_dir = case_dir / "logs"

    for directory in (system_dir, constant_dir, zero_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    case_name = f"{_safe_name(req.vehicle_identity.make)}-{_safe_name(req.vehicle_identity.model)}-{run_id[:8]}"
    runtime_target = str(req.metadata.get("runtime_target", "wsl2"))
    mesh_strategy = "snappyHexMesh" if cad_resolution.selected_source is not None else "blockMesh"
    selected_geometry_uri = cad_resolution.selected_source.uri if cad_resolution.selected_source else (
        cad_resolution.proxy_geometry_uri or cad_resolution.geometry_manifest_uri
    )
    solver_entrypoint = "Allrun"
    case_scaffold_notes = [
        f"Adapter scaffold generated for {case_name}.",
        f"CAD resolver strategy: {cad_resolution.resolved_strategy}.",
        f"Selected geometry URI: {selected_geometry_uri}.",
    ]

    case_files: list[AeroSourceRef] = []
    case_files.append(
        _write_text_artifact(
            case_dir / "README.md",
            "\n".join(
                [
                    f"# OpenFOAM Case Scaffold: {case_name}",
                    "",
                    "This case was scaffolded by MEA and is not yet a solved CFD job.",
                    f"- runtime_target: {runtime_target}",
                    f"- mesh_strategy: {mesh_strategy}",
                    f"- selected_geometry: {selected_geometry_uri}",
                ]
            ),
            label="case_readme",
        )
    )
    case_files.append(
        _write_text_artifact(
            case_dir / "Allrun",
            "\n".join(
                [
                    "#!/bin/sh",
                    "set -eu",
                    "echo 'MEA OpenFOAM scaffold only'",
                    "echo 'Replace this placeholder with the real solver pipeline.'",
                ]
            )
            + "\n",
            label="Allrun",
        )
    )
    case_files.append(
        _write_text_artifact(
            case_dir / "Allclean",
            "\n".join(
                [
                    "#!/bin/sh",
                    "set -eu",
                    "echo 'MEA OpenFOAM scaffold clean step'",
                ]
            )
            + "\n",
            label="Allclean",
        )
    )
    case_files.append(
        _write_text_artifact(
            system_dir / "controlDict",
            _build_control_dict(req, runtime_target),
            label="controlDict",
        )
    )
    case_files.append(
        _write_text_artifact(
            system_dir / "fvSchemes",
            "\n".join(
                [
                    "ddtSchemes",
                    "{",
                    "    default         steadyState;",
                    "}",
                    "",
                    "divSchemes",
                    "{",
                    "    default         none;",
                    "    div(phi,U)      Gauss linearUpwind grad(U);",
                    "}",
                ]
            )
            + "\n",
            label="fvSchemes",
        )
    )
    case_files.append(
        _write_text_artifact(
            system_dir / "fvSolution",
            "\n".join(
                [
                    "solvers",
                    "{",
                    "    p",
                    "    {",
                    "        solver          PCG;",
                    "        tolerance       1e-06;",
                    "    }",
                    "}",
                ]
            )
            + "\n",
            label="fvSolution",
        )
    )
    case_files.append(
        _write_text_artifact(
            constant_dir / "transportProperties",
            "\n".join(
                [
                    "nu              [0 2 -1 0 0 0 0] 1.81e-05;",
                    f"rho             [1 -3 0 0 0 0 0] {req.metadata.get('air_density_kg_m3', 1.225)};",
                ]
            )
            + "\n",
            label="transportProperties",
        )
    )
    case_files.append(
        _write_text_artifact(
            constant_dir / "turbulenceProperties",
            "\n".join(
                [
                    "simulationType  RAS;",
                    "RAS",
                    "{",
                    "    RASModel        kOmegaSST;",
                    "    turbulence      on;",
                    "    printCoeffs     on;",
                    "}",
                ]
            )
            + "\n",
            label="turbulenceProperties",
        )
    )
    case_files.append(
        _write_text_artifact(
            zero_dir / "U",
            "\n".join(
                [
                    "dimensions      [0 1 -1 0 0 0 0];",
                    "internalField   uniform (0 0 0);",
                    "boundaryField   {}",
                ]
            )
            + "\n",
            label="0/U",
        )
    )
    case_files.append(
        _write_text_artifact(
            zero_dir / "p",
            "\n".join(
                [
                    "dimensions      [0 2 -2 0 0 0 0];",
                    "internalField   uniform 0;",
                    "boundaryField   {}",
                ]
            )
            + "\n",
            label="0/p",
        )
    )
    if cad_resolution.selected_source is not None:
        case_files.append(
            _write_text_artifact(
                system_dir / "snappyHexMeshDict",
                "\n".join(
                    [
                        "castellatedMesh true;",
                        "snap            true;",
                        "addLayers       true;",
                        f"geometry        {cad_resolution.selected_source.label or 'selected_cad'};",
                    ]
                )
                + "\n",
                label="snappyHexMeshDict",
            )
        )
    else:
        case_files.append(
            _write_text_artifact(
                system_dir / "blockMeshDict",
                "\n".join(
                    [
                        "convertToMeters 1.0;",
                        "vertices        ();",
                        "blocks          ();",
                        "edges           ();",
                        "boundary        ();",
                    ]
                )
                + "\n",
                label="blockMeshDict",
            )
        )

    case_manifest_payload = {
        "case_name": case_name,
        "case_directory": str(case_dir),
        "runtime_target": runtime_target,
        "requested_strategy": cad_resolution.requested_strategy,
        "resolved_strategy": cad_resolution.resolved_strategy,
        "mesh_strategy": mesh_strategy,
        "scaffold_status": "scaffolded",
        "solver_entrypoint": solver_entrypoint,
        "cad_resolution_uri": cad_resolution.geometry_manifest_uri,
        "selected_geometry_uri": selected_geometry_uri,
        "case_files": [artifact.model_dump(mode="json") for artifact in case_files],
        "notes": case_scaffold_notes,
    }
    case_manifest_path = case_dir / "geometry" / "openfoam_case.json"
    case_manifest_ref = _write_json_artifact(
        case_manifest_path,
        case_manifest_payload,
        label="openfoam_case_manifest",
    )

    return OpenFOAMScaffoldResult(
        case_name=case_name,
        case_directory=str(case_dir),
        runtime_target=runtime_target,
        requested_strategy=cad_resolution.requested_strategy,
        resolved_strategy=cad_resolution.resolved_strategy,
        mesh_strategy=mesh_strategy,
        scaffold_status="scaffolded",
        solver_entrypoint=solver_entrypoint,
        cad_resolution_uri=cad_resolution.geometry_manifest_uri,
        selected_geometry_uri=selected_geometry_uri,
        case_manifest_uri=case_manifest_ref.uri,
        case_manifest_sha256=case_manifest_ref.sha256 or sha256_prefixed(case_manifest_payload),
        case_files=case_files + [case_manifest_ref],
        notes=case_scaffold_notes,
    )
