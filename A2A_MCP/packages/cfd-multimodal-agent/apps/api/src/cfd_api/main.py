from uuid import uuid4

from fastapi import FastAPI

from .models import (
    ImageJobRequest,
    ImageJobResponse,
    PromptPackResponse,
    SimulateRequest,
    SimulateResponse,
)
from .presets import PRESETS
from .simulation import run_simulation

app = FastAPI(title="A2A CFD Multimodal Agent API", version="3.8.0")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/presets")
def list_presets() -> list[dict]:
    return [preset.model_dump() for preset in PRESETS.values()]


@app.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest) -> SimulateResponse:
    return run_simulation(req)


@app.post("/prompt-pack", response_model=PromptPackResponse)
def prompt_pack(req: SimulateRequest) -> PromptPackResponse:
    result = run_simulation(req)
    return PromptPackResponse(prompt_pack=result.prompt_pack)


@app.post("/image-jobs", response_model=ImageJobResponse)
def image_jobs(req: ImageJobRequest) -> ImageJobResponse:
    return ImageJobResponse(
        status="queued",
        job_id=f"job_{uuid4().hex[:12]}",
        provider=req.provider,
    )
