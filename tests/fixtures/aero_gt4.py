from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from shared.forensic_ledger import sha256_prefixed
from shared.models import AeroSourceRef, AeroSimulationRunRequest, AeroVehicleIdentity


FIXTURES_DIR = Path(__file__).resolve().parent
# Use repo-local absolute fixture paths so URIs are valid across CI runners and OSes.
PROFILE_IMAGE_PATH = Path(__file__).resolve()
FRONT_IMAGE_PATH = Path(__file__).resolve()
TELEMETRY_CSV_PATH = (FIXTURES_DIR / "sample_export.csv").resolve()
SPEC_SHEET_URI = "https://manuals.plus/m/e7feaf23c1831eb323faa279d01e5fddf4f184636f782ae88d1f52e8fe07f29d"


def _fixture_uri(path: Path) -> str:
    return path.resolve().as_uri()


def _source_ref(
    *,
    kind: Literal["photo", "cad", "telemetry", "public_reference", "measurement", "wind_tunnel", "solver_case"],
    uri: str,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> AeroSourceRef:
    metadata = metadata or {}
    return AeroSourceRef(
        kind=kind,
        uri=uri,
        label=label,
        sha256=sha256_prefixed({"uri": uri, "label": label, "metadata": metadata}),
        metadata=metadata,
    )


def _base_dimensions() -> dict[str, float]:
    return {
        "length_m": 4.380,
        "width_m": 1.865,
        "width_with_mirrors_m": 2.025,
        "height_m": 1.210,
        "wheelbase_m": 2.600,
        "track_front_m": 1.580,
        "track_rear_m": 1.590,
        "kerb_mass_kg": 1350.0,
    }


def _base_aero_targets() -> dict[str, Any]:
    return {
        "body_style": "front-engine coupe",
        "active_aero": False,
        "front_splitter": "GT4 splitter lip",
        "rear_wing": "GT4 single-plane rear wing",
        "diffuser": "race diffuser",
        "baseline_ride_height_m": 0.045,
        "baseline_yaw_deg": 0.0,
        "baseline_pitch_deg": 0.0,
    }


def _base_parametric_overrides() -> dict[str, Any]:
    return {
        "front_splitter_projection_m": 0.06,
        "rear_wing_angle_deg": 10.0,
        "front_ride_height_m": 0.045,
        "rear_ride_height_m": 0.047,
        "roofline_slope_deg": 7.5,
        "undertray_flat_length_m": 2.18,
    }


def build_gt4_aero_run_request(
    *,
    include_public_cad_candidate: bool = False,
    include_telemetry_source: bool = False,
    baseline_geometry_strategy: Literal["public_cad", "proxy_geometry", "imported_cad", "manual_sketch"] | None = None,
    runtime_target: Literal["sandbox", "wsl2"] = "sandbox",
    runner_kind: Literal["sandbox", "wsl"] = "sandbox",
) -> AeroSimulationRunRequest:
    source_refs: list[AeroSourceRef] = [
        _source_ref(
            kind="photo",
            uri=_fixture_uri(PROFILE_IMAGE_PATH),
            label="gt4-profile-view",
            metadata={"view": "profile", "source": "user-upload"},
        ),
        _source_ref(
            kind="photo",
            uri=_fixture_uri(FRONT_IMAGE_PATH),
            label="gt4-front-view",
            metadata={"view": "front-quarter", "source": "user-upload"},
        ),
        _source_ref(
            kind="public_reference",
            uri=SPEC_SHEET_URI,
            label="aston-martin-vantage-gt4-spec-sheet",
            metadata={
                "publisher": "manuals.plus",
                "document": "aston-martin-racing-vantage-gt4-dimensions",
                "dimensions_verified": True,
            },
        ),
    ]

    if include_public_cad_candidate:
        source_refs.append(
            _source_ref(
                kind="cad",
                uri="s3://cad-library/aston-martin-vantage-gt4.step",
                label="aston-martin-vantage-gt4-public-cad-candidate",
                metadata={
                    "licensed": True,
                    "source": "placeholder-public-cad-candidate",
                    "format": "step",
                },
            )
        )

    if include_telemetry_source:
        source_refs.append(
            _source_ref(
                kind="telemetry",
                uri=_fixture_uri(TELEMETRY_CSV_PATH),
                label="gt4-reference-telemetry",
                metadata={
                    "session_id": "gt4-baseline-session",
                    "source": "user-upload",
                },
            )
        )

    objective = (
        "Build a baseline aero map for an Aston Martin Vantage GT4 proxy, then branch geometry changes "
        "and compare CL/CD quickly."
    )
    if baseline_geometry_strategy is None:
        baseline_geometry_strategy = "public_cad" if include_public_cad_candidate else "proxy_geometry"

    metadata: dict[str, Any] = {
        "dimensions": _base_dimensions(),
        "aero_targets": _base_aero_targets(),
        "runtime_target": runtime_target,
        "runner_kind": runner_kind,
        "reference_velocity_m_s": 55.0,
        "air_density_kg_m3": 1.225,
        "dynamic_viscosity_pa_s": 1.81e-05,
        "reference_pressure_pa": 101325.0,
        "reference_temperature_k": 293.15,
        "reference_area_m2": 2.2608,
        "reference_length_m": 2.6,
        "wsl_distro_name": "Ubuntu-22.04",
        "wsl_distro_version": "22.04",
        "openfoam_version": "11",
        "boundary_conditions": {
            "yaw_deg": 0.0,
            "pitch_deg": 0.0,
            "ride_height_m": 0.045,
            "wheel_rotation": True,
        },
        "snapshot_notes": [
            "Profile image preserves the fastback roofline, long hood, and rear wing profile.",
            "Front-quarter image anchors the splitter, grille opening, and front fender flare.",
            "Dimensions are based on the public Aston Martin Racing GT4 specification sheet.",
        ],
        "topology_notes": [
            "Wide-track GT4 stance retained.",
            "Fastback roofline and rear deck taper preserved in the proxy geometry.",
        ],
        "parametric_overrides": _base_parametric_overrides(),
        "solver_notes": [
            "Use the proxy geometry for deterministic sandbox validation before WSL execution.",
        ],
        "proxy_geometry_notes": [
            "Proxy geometry is anchored to uploaded imagery and public dimensions, not exact CAD.",
        ],
    }

    return AeroSimulationRunRequest(
        project_id="aston-martin-gt4-aero",
        vehicle_program_id="aston-martin-vantage-gt4",
        vehicle_identity=AeroVehicleIdentity(
            make="Aston Martin",
            model="Vantage GT4",
            year=2024,
            trim="AMR GT4",
            chassis_code="Vantage GT4",
            vehicle_class="GT4",
        ),
        source_refs=source_refs,
        simulation_objective=objective,
        baseline_geometry_strategy=baseline_geometry_strategy,
        metadata=metadata,
    )


def build_gt4_aero_run_payload(**kwargs: Any) -> dict[str, Any]:
    return build_gt4_aero_run_request(**kwargs).model_dump(mode="json")
