# CFD Multimodal Agent

## Intent

Provide a fast screening surface that converts vehicle concept parameters into:
- approximate aero metrics
- a pressure-map proxy
- a text prompt pack suitable for downstream multimodal rendering

## API

- `GET /healthz`
- `GET /presets`
- `POST /simulate`
- `POST /prompt-pack`
- `POST /image-jobs`

## Inputs

- vehicle preset
- speed
- yaw
- ride height
- rear wing
- design notes

## Outputs

- drag coefficient
- lift coefficient
- drag force
- lift force
- front/rear downforce split
- Reynolds proxy
- 2D pressure map
- prompt pack

## Boundaries

This is:
- deterministic
- cheap to evaluate
- suitable for UI iteration

This is not:
- full CFD
- mesh-based solving
- signoff-quality engineering analysis
