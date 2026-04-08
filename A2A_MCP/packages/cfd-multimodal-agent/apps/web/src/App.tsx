import { useEffect, useMemo, useState } from "react";
import { simulate } from "./api";

type Preset = "gt" | "prototype" | "road" | "suv";

const PRESET_LABELS: Record<Preset, string> = {
  gt: "GT Car",
  prototype: "Prototype",
  road: "Road Car",
  suv: "SUV"
};

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

function pressureColor(value: number) {
  const hue = value >= 0 ? 8 : 210;
  const sat = 80;
  const light = value >= 0
    ? clamp(84 - value * 28, 34, 84)
    : clamp(80 - Math.abs(value) * 22, 30, 80);

  return `hsl(${hue} ${sat}% ${light}%)`;
}

export default function App() {
  const [preset, setPreset] = useState<Preset>("gt");
  const [speedKph, setSpeedKph] = useState(100);
  const [yawDeg, setYawDeg] = useState(0);
  const [rideHeightMm, setRideHeightMm] = useState(55);
  const [rearWing, setRearWing] = useState(8);
  const [designNotes, setDesignNotes] = useState(
    "Low-slung GT vehicle with clean side flow and technical CFD overlay."
  );
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState("");

  const payload = useMemo(
    () => ({
      preset_id: preset,
      speed_kph: speedKph,
      yaw_deg: yawDeg,
      ride_height_mm: rideHeightMm,
      rear_wing: rearWing,
      design_notes: designNotes
    }),
    [preset, speedKph, yawDeg, rideHeightMm, rearWing, designNotes]
  );

  useEffect(() => {
    simulate(payload)
      .then((data) => {
        setResult(data);
        setError("");
      })
      .catch((e) => {
        setError(String(e));
      });
  }, [payload]);

  return (
    <div className="page">
      <aside className="panel">
        <h1>A2A CFD Multimodal Agent</h1>
        <p className="subtle">Rapid concept screening at 100 kph baseline.</p>

        <label>Vehicle preset</label>
        <div className="buttonGrid">
          {(Object.keys(PRESET_LABELS) as Preset[]).map((key) => (
            <button
              key={key}
              className={key === preset ? "active" : ""}
              onClick={() => setPreset(key)}
            >
              {PRESET_LABELS[key]}
            </button>
          ))}
        </div>

        <label>Speed: {speedKph} kph</label>
        <input
          type="range"
          min="40"
          max="240"
          value={speedKph}
          onChange={(e) => setSpeedKph(Number(e.target.value))}
        />

        <label>Yaw: {yawDeg}°</label>
        <input
          type="range"
          min="-8"
          max="8"
          step="0.1"
          value={yawDeg}
          onChange={(e) => setYawDeg(Number(e.target.value))}
        />

        <label>Ride height: {rideHeightMm} mm</label>
        <input
          type="range"
          min="35"
          max="100"
          step="1"
          value={rideHeightMm}
          onChange={(e) => setRideHeightMm(Number(e.target.value))}
        />

        <label>Rear wing: {rearWing}/20</label>
        <input
          type="range"
          min="0"
          max="20"
          step="1"
          value={rearWing}
          onChange={(e) => setRearWing(Number(e.target.value))}
        />

        <label>Design notes</label>
        <textarea
          value={designNotes}
          onChange={(e) => setDesignNotes(e.target.value)}
          rows={6}
        />

        {error && <div className="error">{error}</div>}
      </aside>

      <main className="main">
        <section className="card">
          <h2>Aero estimate</h2>
          {!result ? (
            <p>Running simulation…</p>
          ) : (
            <div className="stats">
              <div><span>Cd</span><strong>{result.drag_coefficient}</strong></div>
              <div><span>Cl</span><strong>{result.lift_coefficient}</strong></div>
              <div><span>Drag</span><strong>{result.drag_force_n} N</strong></div>
              <div><span>Front DF</span><strong>{result.front_downforce_n} N</strong></div>
              <div><span>Rear DF</span><strong>{result.rear_downforce_n} N</strong></div>
              <div><span>Re</span><strong>{result.reynolds_number}</strong></div>
            </div>
          )}
        </section>

        <section className="card">
          <h2>Pressure map</h2>
          <div className="heatmap">
            {result?.pressure_map?.flatMap((row: number[], r: number) =>
              row.map((v, c) => (
                <div
                  key={`${r}-${c}`}
                  className="cell"
                  style={{ backgroundColor: pressureColor(v) }}
                  title={`Cp ${v}`}
                />
              ))
            )}
          </div>
        </section>

        <section className="card">
          <h2>Prompt pack</h2>
          <pre>{result?.prompt_pack ?? "No prompt generated yet."}</pre>
        </section>
      </main>
    </div>
  );
}
