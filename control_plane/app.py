"""control_plane/app module."""

import ipaddress
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from control_plane.queue import enqueue
from control_plane.repository import create_job, get_job, list_trace
from control_plane.routes.aero import router as aero_router
from control_plane.routes.agent import router as agent_router
from control_plane.routes.ingest import router as ingest_router
from control_plane.routes.replay import router as replay_router
from control_plane.routes.runtime_logs import router as runtime_logs_router
from control_plane.routes.session import router as session_router
from control_plane.routes.verifier import router as verifier_router
from control_plane.webhooks import get_webhook_secret
from control_plane.webhooks import router as github_router
from shared.db import close_pool, pool_health
from shared.forensic_ledger import init_ledger
from shared.models import FixCIRequest
from shared.runtime_paths import default_session_ledger_path
from shared.version import load_version_info

RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
}
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_REQUESTS_PER_WINDOW = int(os.environ.get("RATE_LIMIT_REQUESTS_PER_WINDOW", "60"))
RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS = int(
    os.environ.get("RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS", "30")
)
RATE_LIMIT_PATHS = {
    path.strip()
    for path in os.environ.get("RATE_LIMIT_PATHS", "/repos/fix-ci,/runtime/logs/parse").split(",")
    if path.strip()
}
TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
}
_rate_limit_lock = Lock()
_rate_limit_buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_last_rate_limit_cleanup_at = 0.0
_metrics_lock = Lock()
_metrics = {"requests_total": 0, "rate_limited_total": 0}


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


def _extract_client_ip(request: Request) -> str:
    if TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            for candidate in forwarded_for.split(","):
                candidate_ip = candidate.strip()
                if not candidate_ip:
                    continue
                try:
                    ipaddress.ip_address(candidate_ip)
                    return candidate_ip
                except ValueError:
                    continue
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _prune_bucket(bucket: deque[float], window_start: float) -> None:
    while bucket and bucket[0] < window_start:
        bucket.popleft()


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
    app.state.session_ledger_db_path = validate_session_ledger_startup_config(
        ledger_db_path=ledger_db_path
    )

    yield

    # Shutdown
    close_pool()


app = FastAPI(title="MEA Control Plane", lifespan=lifespan)
app.include_router(github_router)
app.include_router(session_router)
app.include_router(replay_router)
app.include_router(verifier_router)
app.include_router(agent_router)
app.include_router(aero_router)
app.include_router(ingest_router)
app.include_router(runtime_logs_router)

# Serve the premium Google Antigravity Agent Manager UI
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global _last_rate_limit_cleanup_at
    with _metrics_lock:
        _metrics["requests_total"] += 1

    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    if (
        not RATE_LIMIT_ENABLED
        or request.method.upper() != "POST"
        or request.url.path not in RATE_LIMIT_PATHS
    ):
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    client_ip = _extract_client_ip(request)
    now = time.monotonic()
    window_start = now - max(1, RATE_LIMIT_WINDOW_SECONDS)
    bucket_key = (client_ip, request.url.path)
    with _rate_limit_lock:
        cleanup_interval = max(1, RATE_LIMIT_BUCKET_CLEANUP_INTERVAL_SECONDS)
        if now - _last_rate_limit_cleanup_at >= cleanup_interval:
            stale_keys: list[tuple[str, str]] = []
            for key, stale_bucket in _rate_limit_buckets.items():
                _prune_bucket(stale_bucket, window_start)
                if not stale_bucket:
                    stale_keys.append(key)
            for key in stale_keys:
                _rate_limit_buckets.pop(key, None)
            _last_rate_limit_cleanup_at = now

        bucket = _rate_limit_buckets[bucket_key]
        _prune_bucket(bucket, window_start)
        if not bucket:
            _rate_limit_buckets.pop(bucket_key, None)
            bucket = _rate_limit_buckets[bucket_key]
        if len(bucket) >= max(1, RATE_LIMIT_REQUESTS_PER_WINDOW):
            with _metrics_lock:
                _metrics["rate_limited_total"] += 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "rate_limit_exceeded",
                    "path": request.url.path,
                    "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
                    "limit": RATE_LIMIT_REQUESTS_PER_WINDOW,
                    "request_id": request_id,
                },
            )
        bucket.append(now)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/", include_in_schema=False)
def get_agent_manager_window():
    return FileResponse("frontend/index.html")


@app.get("/healthz")
def healthz():
    """Return control-plane liveness and version metadata."""
    version_info = load_version_info()
    return {
        "status": "ok",
        "kernel_version": version_info.kernel_version,
        "package_version": version_info.package_version,
    }


@app.get("/healthz/dependencies")
def healthz_dependencies():
    """Return dependency readiness details used by rollout checks."""
    return {
        "status": "ok",
        "db_pool": pool_health(),
        "session_ledger_db_path": getattr(app.state, "session_ledger_db_path", None),
    }


@app.post("/repos/fix-ci")
def fix_ci(req: FixCIRequest):
    """Queue a fix-ci job for the requested repository and branch."""
    if not req.patch.strip():
        raise HTTPException(status_code=400, detail="Patch is empty")
    payload = req.model_dump()
    job_id = create_job("fix-ci", req.repo, req.branch, payload)
    enqueue({"job_id": job_id, **payload})
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    """Fetch the latest persisted job status payload."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    return job


@app.get("/jobs/{job_id}/trace")
def job_trace(job_id: str):
    """Return trace events recorded for a queued job."""
    trace = list_trace(job_id)
    if not trace:
        raise HTTPException(status_code=404, detail="trace_not_found")
    return trace


@app.get("/metrics")
def metrics():
    """Expose basic Prometheus-style counters for control-plane runtime."""
    with _metrics_lock:
        payload = dict(_metrics)
    lines = [
        f"mea_requests_total {payload['requests_total']}",
        f"mea_rate_limited_total {payload['rate_limited_total']}",
    ]
    return Response(content="\n".join(lines) + "\n", media_type="text/plain")
