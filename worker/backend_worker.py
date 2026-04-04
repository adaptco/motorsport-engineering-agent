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
            req = urllib.request.Request(
                url,
                data=body,
                headers=headers or {},
                method="POST",
            )
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

GITHUB_API_URL = "https://api.github.com"
ALLOWED_REPOS = {r.strip() for r in os.environ.get("GITHUB_ALLOWED_REPOS", "").split(",") if r.strip()}
MAX_PATCH_LINES = int(os.environ.get("MAX_PATCH_LINES", "1000"))
ALLOW_WORKFLOW_CHANGES = os.environ.get("ALLOW_WORKFLOW_CHANGES", "false").lower() == "true"

EMPTY_POLL_BACKOFF_SECONDS_MIN = 1.0
EMPTY_POLL_BACKOFF_SECONDS_MAX = 60.0
WORKER_TEMP_ROOT = Path(os.environ.get("MEA_WORKER_TEMP_ROOT", str(Path.cwd() / ".mea_tmp")))

def run(cmd: list[str], cwd: Path) -> None:
    """
    Execute a shell command in the specified directory.
    Raises subprocess.CalledProcessError if the command fails.
    """
    subprocess.run(cmd, cwd=cwd, check=True)

def validate_patch(patch: str) -> None:
    """
    Validate the incoming patch for security and size constraints.
    
    Checks:
    - Patch is not empty
    - Patch size does not exceed MAX_PATCH_LINES
    - Does not contain sensitive markers (tokens, keys)
    - Workflow changes are allowed only if ALLOW_WORKFLOW_CHANGES is true
    """
    if not patch.strip():
        raise ValueError("Patch is empty")
    if patch.count("\n") > MAX_PATCH_LINES:
        raise ValueError("Patch too large")
    sensitive_markers = ["GITHUB_TOKEN", "BEGIN PRIVATE KEY", "AWS_SECRET_ACCESS_KEY"]
    if any(marker in patch for marker in sensitive_markers):
        raise ValueError("Patch contains sensitive markers")
    if not ALLOW_WORKFLOW_CHANGES and ".github/workflows" in patch:
        raise ValueError("Workflow edits disabled")

def worker_loop():
    """
    Main worker loop that continuously polls for jobs from the queue.
    
    Implements exponential backoff for empty polls to reduce resource usage.
    Processes each job by calling process_fix_ci_job.
    """
    consecutive_empty_polls = 0
    while True:
        job = dequeue()
        if not job:
            consecutive_empty_polls += 1
            sleep_seconds = min(
                EMPTY_POLL_BACKOFF_SECONDS_MAX,
                EMPTY_POLL_BACKOFF_SECONDS_MIN * consecutive_empty_polls,
            )
            if consecutive_empty_polls == 1 or consecutive_empty_polls % 10 == 0:
                logger.info(
                    f"backend_worker_empty_poll: {consecutive_empty_polls} consecutive empty polls, sleeping for {sleep_seconds:.1f}s",
                    extra={
                        "consecutive_empty_polls": consecutive_empty_polls,
                        "sleep_seconds": sleep_seconds,
                    },
                )
            time.sleep(sleep_seconds)
            continue

        consecutive_empty_polls = 0
        process_fix_ci_job(job)

def process_fix_ci_job(job: dict) -> None:
    """
    Process a single CI fix job.
    
    Job processing pipeline:
    1. Validate job identity and repo allowlist
    2. Validate patch security
    3. Obtain GitHub installation token
    4. Clone repository
    5. Apply patch
    6. Run tests
    7. Commit and push changes
    8. Create pull request
    
    Each step updates job phase and adds tracing spans.
    Errors are caught and job is marked as failed.
    """
    job_id = job["job_id"]
    identity = get_job_identity(job_id)
    if not identity:
        return
    trace_id = identity["trace_id"]
    repo_slug = job["repo"]
    base_branch = job["branch"]
    patch = job["patch"]

    try:
        # Step 1: Validate repo is allowlisted
        if repo_slug not in ALLOWED_REPOS:
            raise ValueError("Repo not allowlisted")

        # Step 2: Validate patch
        validate_patch(patch)
        add_span(job_id, trace_id, "policy_check", "ok", {"repo": repo_slug})
        set_job_phase(job_id, "running", "policy_check")

        # Step 3: Get GitHub installation token
        installation_token = get_installation_token(job.get("installation_id"))
        add_span(job_id, trace_id, "issue_installation_token", "ok", {})
        set_job_phase(job_id, "running", "token_issued")

        # Step 4: Clone repository
        WORKER_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmpdir = WORKER_TEMP_ROOT / f"job-{job_id}-{uuid.uuid4().hex[:8]}"
        tmpdir.mkdir(parents=True, exist_ok=False)
        try:
            clone_url = f"https://x-access-token:{installation_token}@github.com/{repo_slug}.git"
            run(["git", "clone", "--depth", "1", "--branch", base_branch, clone_url, "."], cwd=tmpdir)
            add_span(job_id, trace_id, "clone_repo", "ok", {"branch": base_branch})
            set_job_phase(job_id, "running", "cloned")

            # Step 5: Create fix branch and apply patch
            fix_branch = f"fix-ci/{job.get('run_id') or job_id}"
            run(["git", "checkout", "-b", fix_branch], cwd=tmpdir)

            patch_file = tmpdir / "patch.diff"
            patch_file.write_text(patch, encoding="utf-8")
            run(["git", "apply", "patch.diff"], cwd=tmpdir)
            add_span(job_id, trace_id, "apply_patch", "ok", {"patch_hash": hashlib.sha256(patch.encode()).hexdigest()})
            set_job_phase(job_id, "running", "patched")

            # Step 6: Run tests
            tests_ok = True
            try:
                run(["pytest"], cwd=tmpdir)
            except subprocess.CalledProcessError:
                tests_ok = False
            add_span(job_id, trace_id, "test_suite", "ok" if tests_ok else "warning", {"tests_ok": tests_ok})
            if not tests_ok:
                set_job_phase(
                    job_id,
                    "failed",
                    "validation_failed",
                    {"tests_ok": False},
                    error_message="Validation failed: test suite failed",
                )
                return
            set_job_phase(job_id, "running", "validated", {"tests_ok": True})

            run(["git", "config", "user.name", "mea-ci-bot[app]"], cwd=tmpdir)
            run(["git", "config", "user.email", "mea-ci-bot@example.com"], cwd=tmpdir)
            run(["git", "add", "."], cwd=tmpdir)
            run(["git", "commit", "-m", f"Fix CI run {job.get('run_id') or job_id}"], cwd=tmpdir)
            run(["git", "push", "origin", fix_branch], cwd=tmpdir)
            add_span(job_id, trace_id, "push_branch", "ok", {"fix_branch": fix_branch})
            set_job_phase(job_id, "running", "pushed")

            # Step 8: Create pull request
            owner, repo_name = repo_slug.split("/")
            resp = requests.post(
                f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/pulls",
                headers={
                    "Authorization": f"Bearer {installation_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "title": f"[MEA CI Bot] Fix CI for {job.get('run_id') or job_id}",
                    "head": fix_branch,
                    "base": base_branch,
                    "body": "Automated CI fix created by the MEA backend worker.",
                    "maintainer_can_modify": True,
                },
                timeout=30,
            )
            resp.raise_for_status()
            pr = resp.json()
            pr_url = pr["html_url"]
            add_span(job_id, trace_id, "create_pr", "ok", {"pr_url": pr_url})
            complete_job(job_id, fix_branch, pr_url, {"summary": "PR opened", "tests_ok": tests_ok, "pr_url": pr_url})
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        # Error handling: Mark job as failed and log error
        set_job_phase(job_id, "failed", "error", error_message=str(e))
        if identity:
            add_span(job_id, trace_id, "job_error", "error", {"error": str(e)})

if __name__ == "__main__":
    worker_loop()
