import hashlib
import json as jsonlib
import logging
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

# --- INFRASTRUCTURE: REQUESTS FALLBACK ---
try:
    import requests
except ModuleNotFoundError:
    class _FallbackResponse:
        def __init__(self, status_code: int, payload: dict):
            self.status_code = status_code
            self._payload = payload
        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}: {self._payload}")
        def json(self) -> dict:
            return self._payload

    class _FallbackRequests:
        @staticmethod
        def post(url: str, headers: dict | None = None, json: dict | None = None, timeout: int = 30) -> _FallbackResponse:
            body = None if json is None else str.encode(jsonlib.dumps(json), "utf-8")
            req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    payload_bytes = resp.read()
                    payload = jsonlib.loads(payload_bytes.decode("utf-8")) if payload_bytes else {}
                    status_code = getattr(resp, "status", resp.getcode())
                    return _FallbackResponse(status_code, payload)
            except urllib.error.HTTPError as http_error:
                payload = {}
                if http_error.fp:
                    payload = jsonlib.loads(http_error.fp.read().decode("utf-8"))
                return _FallbackResponse(http_error.code, payload)
    requests = _FallbackRequests()

from control_plane.queue import dequeue
from worker.github_app_client import get_installation_token
from worker.repository import add_span, complete_job, get_job_identity, set_job_phase

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
GITHUB_API_URL = "https://api.github.com"
ALLOWED_REPOS = {r.strip() for r in os.environ.get("GITHUB_ALLOWED_REPOS", "").split(",") if r.strip()}
MAX_PATCH_LINES = int(os.environ.get("MAX_PATCH_LINES", "1000"))
ALLOW_WORKFLOW_CHANGES = os.environ.get("ALLOW_WORKFLOW_CHANGES", "false").lower() == "true"
EMPTY_POLL_BACKOFF_SECONDS_MIN = 1.0
EMPTY_POLL_BACKOFF_SECONDS_MAX = 60.0
WORKER_TEMP_ROOT = Path(os.environ.get("MEA_WORKER_TEMP_ROOT", str(Path.cwd() / ".mea_tmp")))

@asynccontextmanager
async def lifespan(app):
    """ASGI Lifespan for production process management."""
    logger.info("MEA Worker: Initializing Infrastructure")
    WORKER_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("MEA Worker: Cleaning up temporary artifacts")
    if WORKER_TEMP_ROOT.exists():
        shutil.rmtree(WORKER_TEMP_ROOT, ignore_errors=True)

def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)

def validate_patch_integrity(patch: str) -> None:
    if not patch:
        raise ValueError("Rejecting empty patch artifact")
    if patch.count("\n") > MAX_PATCH_LINES:
        raise ValueError(f"Patch length exceeds limit of {MAX_PATCH_LINES} lines")
    if not ALLOW_WORKFLOW_CHANGES and ".github/workflows" in patch:
        raise ValueError("Security Policy: Workflow modifications are restricted")

def process_fix_ci_job(job: dict) -> None:
    job_id = job["job_id"]
    identity = get_job_identity(job_id)
    if not identity:
        logger.error(f"Critical: Identity not found for Job ID {job_id}")
        return

    trace_id = identity["trace_id"]
    repo_slug = job["repo"]
    base_branch = job.get("branch", "main")
    patch_data = job.get("patch", "")

    try:
        if repo_slug not in ALLOWED_REPOS:
            raise PermissionError(f"Repository {repo_slug} is not in the allowlist")
        
        validate_patch_integrity(patch_data)

        # FIXED: 5 args (job_id, trace_id, span_name, status, attributes)
        add_span(job_id, trace_id, "policy_check", "ok", {"repo": repo_slug})
        # FIXED: 5 args (job_id, status, phase, payload, error_message)
        set_job_phase(job_id, "running", "policy_check", {"repo": repo_slug}, None)

        token = get_installation_token(job.get("installation_id"))
        set_job_phase(job_id, "running", "token_acquired", {}, None)

        job_dir = WORKER_TEMP_ROOT / f"job-{job_id}-{uuid.uuid4().hex[:6]}"
        job_dir.mkdir(parents=True, exist_ok=False)

        try:
            # 1. Environment Setup
            clone_url = f"https://x-access-token:{token}@github.com/{repo_slug}.git"
            run_command(["git", "clone", "--depth", "1", "--branch", base_branch, "--", clone_url, "."], cwd=job_dir)
            
            add_span(job_id, trace_id, "clone_operation", "ok", {"branch": base_branch})
            set_job_phase(job_id, "running", "environment_ready", {}, None)

            # 2. Patch Execution
            fix_branch = f"mea-fix/{job_id}"
            run_command(["git", "checkout", "-b", fix_branch], cwd=job_dir)
            
            patch_file = job_dir / "incoming.patch"
            patch_file.write_text(patch_data, encoding="utf-8")
            run_command(["git", "apply", "incoming.patch"], cwd=job_dir)
            
            set_job_phase(job_id, "running", "patch_applied", {"hash": hashlib.sha256(patch_data.encode()).hexdigest()}, None)

            # 3. Deterministic Validation
            set_job_phase(job_id, "running", "testing", {}, None)
            test_result = subprocess.run(["pytest", "-v"], cwd=job_dir, capture_output=True, text=True)
            
            add_span(job_id, trace_id, "test_validation", "ok" if test_result.returncode == 0 else "fail", {"code": test_result.returncode})

            if test_result.returncode != 0:
                set_job_phase(job_id, "failed", "test_regression", {"stdout": test_result.stdout}, "Patch failed test validation")
                return

            # 4. Artifact Submission
            run_command(["git", "config", "user.name", "mea-bot"], cwd=job_dir)
            run_command(["git", "config", "user.email", "mea-bot@adaptco.ai"], cwd=job_dir)
            run_command(["git", "add", "."], cwd=job_dir)
            run_command(["git", "commit", "-m", f"Fix for CI Job {job_id}"], cwd=job_dir)
            run_command(["git", "push", "origin", fix_branch], cwd=job_dir)

            owner, name = repo_slug.split("/")
            pr_resp = requests.post(
                f"{GITHUB_API_URL}/repos/{owner}/{name}/pulls",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": f"CI Fix: {job_id}", "head": fix_branch, "base": base_branch},
            )
            pr_resp.raise_for_status()
            pr_url = pr_resp.json()["html_url"]

            add_span(job_id, trace_id, "pr_submission", "ok", {"pr_url": pr_url})
            # FIXED: 4 args (job_id, fix_branch, pr_url, result_payload)
            complete_job(job_id, fix_branch, pr_url, {"status": "success"})

        finally:
            shutil.rmtree(job_dir, ignore_errors=True)

    except Exception as e:
        logger.exception(f"Processing Failure for Job {job_id}")
        # FIXED: 5 args (job_id, status, phase, payload, error_message)
        set_job_phase(job_id, "failed", "system_error", {"exception": str(e)}, str(e))

def worker_main():
    """Main worker loop with exponential backoff."""
    backoff = 0
    logger.info("MEA Backend Worker operational")
    while True:
        try:
            job = dequeue()
            if not job:
                backoff = min(EMPTY_POLL_BACKOFF_SECONDS_MAX, backoff + 1)
                time.sleep(backoff)
                continue
            backoff = 0
            process_fix_ci_job(job)
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    worker_main()
