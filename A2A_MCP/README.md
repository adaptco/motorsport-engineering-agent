# A2A_MCP

V3.8 adds a bounded multimodal CFD concept-screening module under `packages/cfd-multimodal-agent`.

## V3.8 scope

- deterministic surrogate CFD screening service
- React control surface for concept tuning
- shared TS contracts
- prompt-pack generation for downstream image workflows
- docker compose entrypoint for local bring-up

## Paths

- `packages/cfd-multimodal-agent/apps/api` — FastAPI service
- `packages/cfd-multimodal-agent/apps/web` — React/Vite frontend
- `packages/cfd-contracts` — shared TS contracts
- `docs/v3.8` — V3.8 design and migration notes

## Notes

This module is a rapid concept-screening subsystem. It is not production CFD and must not be treated as engineering signoff.
