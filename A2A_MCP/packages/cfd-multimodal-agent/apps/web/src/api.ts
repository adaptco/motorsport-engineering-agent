const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type SimulateRequest = {
  preset_id: "gt" | "prototype" | "road" | "suv";
  speed_kph: number;
  yaw_deg: number;
  ride_height_mm: number;
  rear_wing: number;
  design_notes?: string;
};

export async function simulate(payload: SimulateRequest) {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error("Simulation request failed");
  }

  return res.json();
}
