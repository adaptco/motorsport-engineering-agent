import subprocess
import pytest
from worker import backend_worker
from worker import repository as repo

def test_process_fix_ci_job_fails_validation(monkeypatch):
    calls = {"phases": []}
    
    # Mocking the namespace targets
    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"acme/repo"})
    monkeypatch.setattr(backend_worker.gh, "get_installation_token", lambda id: "token")
    monkeypatch.setattr(repo, "get_job_identity", lambda id: {"trace_id": "t1"})
    monkeypatch.setattr(repo, "add_span", lambda *a, **k: None)
    monkeypatch.setattr(repo, "set_job_phase", lambda *a, **k: calls["phases"].append(a))

    # Trigger failure
    monkeypatch.setattr(backend_worker, "run", lambda cmd, cwd: subprocess.check_call(["false"]) if "pytest" in cmd else None)

    job = {"job_id": "j1", "repo": "acme/repo", "branch": "main", "patch": "diff...", "installation_id": 1}
    backend_worker.process_fix_ci_job(job)

    assert any("validation_failed" in str(p) for p in calls["phases"])
