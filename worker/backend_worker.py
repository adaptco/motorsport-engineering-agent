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

# Fallback for requests if not in environment
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
                    raw = http_error.fp.read().decode("utf-8")
                    try:
                        payload = jsonlib.loads(raw) if raw else {}
                    except jsonlib.JSONDecodeError:
                        payload = {"message": raw}
                return _FallbackResponse(http_error.code, payload)
    requests = _FallbackRequests()

from control_plane.queue import dequeue
from worker import github_app_client as gh
from worker import repository as repo

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
ALLOWED_REPOS = {r.strip() for r in os.environ.get("GITHUB_ALLOWED_REPOS", "").split(",") if r.strip()}
MAX_PATCH_LINES = int(os.environ.get("MAX_PATCH_LINES", "1000"))
ALLOW_WORKFLOW_CHANGES = os.environ.get("ALLOW_WORKFLOW_CHANGES", "false").lower() == "true"
WORKER_TEMP_ROOT = Path(os.environ.get("MEA_WORKER_TEMP_ROOT", str(Path.cwd() / ".mea_tmp")))

def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)

def validate_patch(patch: str) -> None:
    if not patch.strip():
        raise ValueError("Patch is empty")
    if patch.count("\n") > MAX_PATCH_LINES:
        raise ValueError("Patch too large")
    if not ALLOW_WORKFLOW_CHANGES and ".github/workflows" in patch:
        raise ValueError("Workflow edits disabled")

def process_fix_ci_job(job: dict) -> None:
    job_id = job["job_id"]
    identity = repo.get_job_identity(job_id)
    if not identity:
        return

    trace_id = identity["trace_id"]
    repo_slug = job["repo"]
    base_branch = job["branch"]
    patch = job["patch"]

    try:
        # Validation & Policy
        if repo_slug not in ALLOWED_REPOS:
            raise ValueError("Repo not allowlisted")
        validate_patch(patch)
        repo.add_span(job_id, trace_id, "policy_check", "ok", {"repo": repo_slug})
        repo.set_job_phase(job_id, "running", "policy_check")

        # Auth
        installation_token = gh.get_installation_token(job.get("installation_id"))
        repo.add_span(job_id, trace_id, "issue_installation_token", "ok", {})
        repo.set_job_phase(job_id, "running", "token_issued")

        # Workspace Setup
        WORKER_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        tmpdir = WORKER_TEMP_ROOT / f"job-{job_id}-{uuid.uuid4().hex[:8]}"
        tmpdir.mkdir(parents=True, exist_ok=False)

        try:
            # Git Operations
            clone_url = f"https://x-access-token:{installation_token}@github.com/{repo_slug}.git"
            run(["git", "clone", "--depth", "1", "--branch", base_branch, "--", clone_url, "."], cwd=tmpdir)
            repo.set_job_phase(job_id, "running", "cloned")

            fix_branch = f"fix-ci/{job.get('run_id') or job_id}"
            run(["git", "checkout", "-b", fix_branch], cwd=tmpdir)
            (tmpdir / "patch.diff").write_text(patch, encoding="utf-8")
            run(["git", "apply", "patch.diff"], cwd=tmpdir)
            repo.set_job_phase(job_id, "running", "patched")

            # Tests
            tests_ok = True
            try:
                run(["pytest"], cwd=tmpdir)
            except subprocess.CalledProcessError:
                tests_ok = False
            
            repo.add_span(job_id, trace_id, "test_suite", "ok" if tests_ok else "warning", {"tests_ok": tests_ok})
            if not tests_ok:
                repo.set_job_phase(job_id, "failed", "validation_failed", error_message="Tests failed")
                return
            
            repo.set_job_phase(job_id, "running", "validated")

            # Push & PR
            run(["git", "config", "user.name", "mea-ci-bot"], cwd=tmpdir)
            run(["git", "config", "user.email", "mea-ci-bot@example.com"], cwd=tmpdir)
            run(["git", "add", "."], cwd=tmpdir)
            run(["git", "commit", "-m", f"Fix CI {job_id}"], cwd=tmpdir)
            run(["git", "push", "origin", fix_branch], cwd=tmpdir)
            
            owner, name = repo_slug.split("/")
            resp = requests.post(
                f"{GITHUB_API_URL}/repos/{owner}/{name}/pulls",
                headers={"Authorization": f"Bearer {installation_token}"},
                json={"title": f"Fix CI {job_id}", "head": fix_branch, "base": base_branch},
            )
            resp.raise_for_status()
            pr_url = resp.json()["html_url"]
            
            repo.complete_job(job_id, fix_branch, pr_url, {"summary": "PR opened"})

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        repo.set_job_phase(job_id, "failed", "error", error_message=str(e))
