# Aero Simulation Service

This service is the dedicated aerodynamic simulation layer for MEA.

It is separate from the racing telemetry loop and should own:
- vehicle snapshot normalization
- public CAD / geometry candidate resolution via `control_plane/services/cad_resolver.py`
- OpenFOAM case generation via `control_plane/services/openfoam_adapter.py`
- deterministic sandbox execution for unit tests and baseline state validation
- gated WSL2 or Linux VM execution orchestration for OpenFOAM solves
- CL / CD branch evaluation and calibration history

The durable state contract for this lane lives under `contracts/aero/` and the control-plane API boundary lives under `control_plane/routes/aero.py`.
