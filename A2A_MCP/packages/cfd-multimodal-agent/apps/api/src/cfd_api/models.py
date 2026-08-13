from typing import Literal

from pydantic import BaseModel, Field

VehiclePresetId = Literal["gt", "prototype", "road", "suv"]


class SimulateRequest(BaseModel):
    preset_id: VehiclePresetId = Field(default="gt")
    speed_kph: float = Field(default=100, ge=1, le=400)
    yaw_deg: float = Field(default=0, ge=-20, le=20)
    ride_height_mm: float = Field(default=55, ge=20, le=200)
    rear_wing: float = Field(default=8, ge=0, le=20)
    design_notes: str = Field(default="")


class VehiclePreset(BaseModel):
    id: VehiclePresetId
    name: str
    cd: float
    area: float
    lift_bias: float
    body_scale_x: float
    body_scale_y: float
    canopy: float
    tail: float


class SimulateResponse(BaseModel):
    speed_mps: float
    dynamic_pressure_pa: float
    drag_coefficient: float
    lift_coefficient: float
    drag_force_n: float
    lift_force_n: float
    front_downforce_n: float
    rear_downforce_n: float
    reynolds_number: float
    pressure_map: list[list[float]]
    prompt_pack: str


class PromptPackResponse(BaseModel):
    prompt_pack: str


class ImageJobRequest(BaseModel):
    prompt: str
    provider: str = "placeholder"


class ImageJobResponse(BaseModel):
    status: str
    job_id: str
    provider: str
