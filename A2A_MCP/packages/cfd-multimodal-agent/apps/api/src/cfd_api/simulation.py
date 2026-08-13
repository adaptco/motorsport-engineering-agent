from math import exp

from .models import SimulateRequest, SimulateResponse
from .presets import PRESETS

RHO = 1.225
KPH_TO_MPS = 1000 / 3600
KINEMATIC_VISCOSITY = 1.5e-5
REFERENCE_LENGTH_M = 4.5


def clamp(value: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, value))


def build_prompt_pack(
    req: SimulateRequest,
    *,
    speed_mps: float,
    cd_eff: float,
    cl_eff: float,
    drag_n: float,
    lift_n: float,
) -> str:
    preset = PRESETS[req.preset_id]
    return "\n".join(
        [
            f"Vehicle concept: {preset.name}",
            f"Speed: {req.speed_kph:.0f} kph ({speed_mps:.2f} m/s)",
            f"Yaw: {req.yaw_deg:.1f} degrees",
            f"Ride height: {req.ride_height_mm:.0f} mm",
            f"Rear wing setting: {req.rear_wing:.0f}/20",
            f"Estimated drag coefficient: {cd_eff:.3f}",
            f"Estimated lift coefficient: {cl_eff:.3f}",
            f"Estimated drag force: {drag_n:.1f} N",
            f"Estimated net downforce: {-lift_n:.1f} N",
            f"Design notes: {req.design_notes or 'none'}",
            "Render request: studio side profile plus translucent CFD pressure overlay, blue low-pressure zones, red stagnation zones, clean technical visualization.",
        ]
    )


def generate_pressure_map(yaw_deg: float, cd_eff: float) -> list[list[float]]:
    cp_base = 1 - cd_eff
    rows: list[list[float]] = []

    for iy in range(48):
        row: list[float] = []
        for ix in range(96):
            x = ix / 95
            y = iy / 47

            body = exp(-(((x - 0.46) / 0.24) ** 2 + ((y - 0.50) / 0.28) ** 2))
            nose_peak = 1.35 * exp(-(((x - 0.20) / 0.09) ** 2 + ((y - 0.50) / 0.18) ** 2))
            roof_suction = -0.80 * exp(-(((x - 0.50) / 0.16) ** 2 + ((y - 0.30) / 0.12) ** 2))
            diffuser = -0.72 * exp(-(((x - 0.82) / 0.16) ** 2 + ((y - 0.68) / 0.14) ** 2))
            wake = -0.50 * exp(-(((x - 0.95) / 0.12) ** 2 + ((y - 0.50) / 0.22) ** 2))
            yaw_field = ((x - 0.40) * (y - 0.50) * yaw_deg) / 16

            cp = clamp(
                (cp_base * body + nose_peak + roof_suction + diffuser + wake + yaw_field) * 0.85,
                -1.4,
                1.6,
            )
            row.append(round(cp, 4))
        rows.append(row)

    return rows


def run_simulation(req: SimulateRequest) -> SimulateResponse:
    preset = PRESETS[req.preset_id]
    speed_mps = req.speed_kph * KPH_TO_MPS
    q = 0.5 * RHO * speed_mps * speed_mps
    yaw = abs(req.yaw_deg) / 10
    ride = clamp((req.ride_height_mm - 45) / 35, -0.6, 1.4)
    wing = req.rear_wing / 20

    cd_eff = preset.cd * (1 + yaw * 0.20 + wing * 0.08 + max(0, ride) * 0.05)
    cl_eff = preset.lift_bias - wing * 0.48 + max(0, 0.18 - ride * 0.08) - yaw * 0.04

    drag_n = q * preset.area * cd_eff
    lift_n = q * preset.area * cl_eff

    front_share = clamp(0.52 + wing * -0.10 + ride * 0.03, 0.38, 0.62)
    front_downforce = -lift_n * front_share
    rear_downforce = -lift_n * (1 - front_share)
    reynolds = speed_mps * REFERENCE_LENGTH_M / KINEMATIC_VISCOSITY

    pressure_map = generate_pressure_map(req.yaw_deg, cd_eff)
    prompt_pack = build_prompt_pack(
        req,
        speed_mps=speed_mps,
        cd_eff=cd_eff,
        cl_eff=cl_eff,
        drag_n=drag_n,
        lift_n=lift_n,
    )

    return SimulateResponse(
        speed_mps=round(speed_mps, 4),
        dynamic_pressure_pa=round(q, 4),
        drag_coefficient=round(cd_eff, 4),
        lift_coefficient=round(cl_eff, 4),
        drag_force_n=round(drag_n, 4),
        lift_force_n=round(lift_n, 4),
        front_downforce_n=round(front_downforce, 4),
        rear_downforce_n=round(rear_downforce, 4),
        reynolds_number=round(reynolds, 2),
        pressure_map=pressure_map,
        prompt_pack=prompt_pack,
    )
