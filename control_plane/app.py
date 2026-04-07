import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from control_plane.queue import enqueue
from control_plane.routes.agent import router as agent_router
from control_plane.routes.ingest import router as ingest_router
from control_plane.routes.runtime_logs import router as runtime_logs_router
from control_plane.repository import create_job, get_job, list_trace
from control_plane.routes.replay import router as replay_router
from control_plane.routes.session import router as session_router
from control_plane.routes.verifier import router as verifier_router
from control_plane.webhooks import get_webhook_secret, router as github_router
from shared.db import close_pool, pool_health
from shared.forensic_ledger import init_ledger
from shared.models import FixCIRequest
from shared.runtime_paths import default_session_ledger_path
from shared.version import load_version_info


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


def validate_webhook_startup_config(*, webhook_secret: str | None, webhook_required: bool) -> bool:
    if webhook_required and not webhook_secret:
        raise RuntimeError("GITHUB_WEBHOOK_SECRET must be set when GITHUB_WEBHOOK_REQUIRED is true")
    return bool(webhook_secret)


def validate_session_ledger_startup_config(*, ledger_db_path: str | Path) -> str:
    ledger_path = Path(ledger_db_path).expanduser()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    init_ledger(ledger_path)
    if not ledger_path.exists():
        raise RuntimeError(f"SESSION_LEDGER_DB_PATH is not writable: {ledger_path}")
    return str(ledger_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    webhook_secret = get_webhook_secret()
    webhook_required = _is_truthy(os.environ.get("GITHUB_WEBHOOK_REQUIRED"))
    app.state.github_webhook_configured = validate_webhook_startup_config(
        webhook_secret=webhook_secret,
        webhook_required=webhook_required,
    )
    ledger_db_path = os.environ.get("SESSION_LEDGER_DB_PATH", str(default_session_ledger_path()))
    app.state.session_ledger_db_path = validate_session_ledger_startup_config(ledger_db_path=ledger_db_path)

    yield

    # Shutdown
    close_pool()


app = FastAPI(title="MEA Control Plane", lifespan=lifespan)
app.include_router(github_router)
app.include_router(session_router)
app.include_router(replay_router)
app.include_router(verifier_router)
app.include_router(agent_router)
app.include_router(ingest_router)
app.include_router(runtime_logs_router)

# Serve the premium Google Antigravity Agent Manager UI
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
def get_agent_manager_window():
    return FileResponse("frontend/index.html")


@app.get("/healthz")
def healthz():
    version_info = load_version_info()
    return {
        "status": "ok",
        "kernel_version": version_info.kernel_version,
        "package_version": version_info.package_version,
    }


@app.get("/healthz/dependencies")
def healthz_dependencies():
    return {
        "status": "ok",
        "db_pool": pool_health(),
        "session_ledger_db_path": getattr(app.state, "session_ledger_db_path", None),
    }


@app.post("/repos/fix-ci")
def fix_ci(req: FixCIRequest):
    if not req.patch.strip():
        raise HTTPException(status_code=400, detail="Patch is empty")
    payload = req.model_dump()
    job_id = create_job("fix-ci", req.repo, req.branch, payload)
    enqueue({"job_id": job_id, **payload})
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    return job


@app.get("/jobs/{job_id}/trace")
def job_trace(job_id: str):
    trace = list_trace(job_id)
    if not trace:
        raise HTTPException(status_code=404, detail="trace_not_found")
    return trace
