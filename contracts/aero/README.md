# Aero Simulation Contract Surface

This directory defines the durable state contract for MEA's aerodynamic simulation lane.

## Boundary
- The racing telemetry loop owns session evidence, replay, and on-track analysis.
- The aero simulation lane owns vehicle snapshots, geometry baselines, solver state, CL/CD evaluation, and design branches.
- Telemetry references may be linked as inputs, but telemetry session state is not reused as the aero state of record.

## API Surface
- `POST /aero/runs`
- `GET /aero/runs`
- `GET /aero/runs/{run_id}`
- `POST /aero/runs/{run_id}/branches`

## State Location
- Default local state root: `.mea_tmp/aero_state/`
- Override with `AERO_STATE_ROOT`

## Contract Files
- `aero_simulation_state.schema.json`: durable state record for the aero lane

## Persisted Artifacts
- `geometry/cad_resolution.json`: selected CAD or proxy resolution for the run
- `geometry/openfoam_case.json`: scaffolded OpenFOAM case manifest
- `system/`, `constant/`, `0/`: generated solver case files under the run directory
