# V3.8 Architecture

## Objective

Add a contained multimodal concept-screening lane into the A2A_MCP monorepo without coupling it to the orchestration kernel.

## Planes

### 1. Simulation plane
- surrogate aero estimator
- pressure proxy generation
- deterministic preset catalog

### 2. Multimodal plane
- prompt-pack generation from simulation state
- image-job request surface
- downstream provider placeholder integration point

### 3. Interface plane
- React control surface
- parameter sliders
- pressure-map visualization
- prompt-pack inspection

## Integration stance

This V3.8 module is intentionally isolated:
- no runtime mutation of core A2A orchestration contracts
- no coupling to existing agent registry paths
- no governance receipt assumptions yet
- can later be wrapped as a tool surface within MCP

## Next recommended hardening

1. Add receipt emission for simulation inputs/outputs
2. Add request hashing for deterministic replay
3. Persist scenarios and result bundles
4. Add provider abstraction for image generation
5. Add policy boundary before external image-job dispatch
