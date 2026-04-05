import logging
import os
import uuid
import shutil
import subprocess
from pathlib import Path
from worker import github_app_client as gh
from worker import repository as repo  # Namespaced import

logger = logging.getLogger(__name__)

def process_fix_ci_job(job: dict) -> None:
    job_id = job["job_id"]
    # 1. Grounded call to get_job_identity
    identity = repo.get_job_identity(job_id)
    if not identity:
        return

    trace_id = identity["trace_id"]
    repo_slug = job["repo"]
    
    try:
        # 2. Grounded call to set_job_phase (matching 5-arg signature)
        repo.set_job_phase(job_id, "running", "policy_check", {"repo": repo_slug}, None)
        repo.add_span(job_id, trace_id, "policy_check", "ok", {"repo": repo_slug})

        # ... (rest of your logic) ...

        # 3. Grounded call to complete_job
        repo.complete_job(job_id, "fix-branch-name", "https://github.com/pr/1", {"status": "done"})

    except Exception as e:
        # 4. Grounded error handling
        repo.set_job_phase(job_id, "failed", "error", None, str(e))
