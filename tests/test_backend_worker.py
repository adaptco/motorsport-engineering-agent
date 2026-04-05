from worker import backend_worker
from worker import repository as repo

def test_process_fix_ci_job_flow(monkeypatch):
    # Mock the 'repo' object directly so the worker finds it
    monkeypatch.setattr(repo, "get_job_identity", lambda id: {"trace_id": "t1", "repo_slug": "ok/repo", "base_branch": "main"})
    monkeypatch.setattr(repo, "set_job_phase", lambda *a, **k: None)
    monkeypatch.setattr(repo, "add_span", lambda *a, **k: None)
    monkeypatch.setattr(repo, "complete_job", lambda *a, **k: None)
    
    job = {"job_id": "j1", "repo": "ok/repo", "branch": "main", "patch": "diff"}
    backend_worker.process_fix_ci_job(job)
