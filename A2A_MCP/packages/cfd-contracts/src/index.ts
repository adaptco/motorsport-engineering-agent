export type VehiclePresetId = "gt" | "prototype" | "road" | "suv";

export interface SimulateRequest {
  preset_id: VehiclePresetId;
  speed_kph: number;
  yaw_deg: number;
  ride_height_mm: number;
  rear_wing: number;
  design_notes?: string;
}

export interface SimulateResponse {
  speed_mps: number;
  dynamic_pressure_pa: number;
  drag_coefficient: number;
  lift_coefficient: number;
  drag_force_n: number;
  lift_force_n: number;
  front_downforce_n: number;
  rear_downforce_n: number;
  reynolds_number: number;
  pressure_map: number[][];
  prompt_pack: string;
}

export interface PromptPackResponse {
  prompt_pack: string;
}

export interface ImageJobRequest {
  prompt: string;
  provider?: string;
}

export interface ImageJobResponse {
  status: string;
  job_id: string;
  provider: string;
}
