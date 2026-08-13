from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from worker import backend_worker
from worker import github_app_client as gh
from worker import repository as repo


def test_validate_patch_constraints() -> None:
    # 1. Empty patch
    with pytest.raises(ValueError, match="Patch is empty"):
        backend_worker.validate_patch("   ")

    # 2. Patch too large
    large_patch = "\n".join(["line"] * 1005)
    with pytest.raises(ValueError, match="Patch too large"):
        backend_worker.validate_patch(large_patch)

    # 3. Sensitive markers
    with pytest.raises(ValueError, match="Patch contains sensitive markers"):
        backend_worker.validate_patch("diff --git\n+GITHUB_TOKEN=xyz")

    with pytest.raises(ValueError, match="Patch contains sensitive markers"):
        backend_worker.validate_patch("diff --git\n+BEGIN PRIVATE KEY")

    with pytest.raises(ValueError, match="Patch contains sensitive markers"):
        backend_worker.validate_patch("diff --git\n+AWS_SECRET_ACCESS_KEY")

    # 4. Workflow edits when disabled
    with pytest.raises(ValueError, match="Workflow edits disabled"):
        backend_worker.validate_patch(
            "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml"
        )

    # 5. Valid patch
    backend_worker.validate_patch("diff --git a/src/app.py b/src/app.py\n+print('hello')\n")


def test_run_command_success_and_failure(tmp_path: Path) -> None:
    # Success
    backend_worker.run(["python", "-c", "print(1)"], cwd=tmp_path)

    # Failure
    with pytest.raises(subprocess.CalledProcessError):
        backend_worker.run(["python", "-c", "import sys; sys.exit(1)"], cwd=tmp_path)


def test_process_fix_ci_job_flow(monkeypatch):
    # Mock the 'repo' object directly so the worker finds it
    monkeypatch.setattr(
        repo,
        "get_job_identity",
        lambda id: {"trace_id": "t1", "repo_slug": "ok/repo", "base_branch": "main"},
    )
    monkeypatch.setattr(repo, "set_job_phase", lambda *a, **k: None)
    monkeypatch.setattr(repo, "add_span", lambda *a, **k: None)
    monkeypatch.setattr(repo, "complete_job", lambda *a, **k: None)

    job = {"job_id": "j1", "repo": "ok/repo", "branch": "main", "patch": "diff"}
    backend_worker.process_fix_ci_job(job)


def test_process_fix_ci_job_unallowed_repo(monkeypatch) -> None:
    monkeypatch.setattr(
        repo,
        "get_job_identity",
        lambda jid: {"trace_id": "t1", "repo_slug": "unauthorized/repo", "base_branch": "main"},
    )
    phase_mock = MagicMock()
    monkeypatch.setattr(repo, "set_job_phase", phase_mock)
    monkeypatch.setattr(repo, "add_span", MagicMock())

    job = {"job_id": "j1", "repo": "unauthorized/repo", "branch": "main", "patch": "diff"}
    backend_worker.process_fix_ci_job(job)
    phase_mock.assert_called_with(
        "j1", "failed", "error", {"exception": "<class 'ValueError'>"}, "Repo not allowlisted"
    )


def test_process_fix_ci_job_success_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"org/repo"})
    monkeypatch.setattr(backend_worker, "WORKER_TEMP_ROOT", tmp_path / "worker_tmp")
    monkeypatch.setattr(
        repo,
        "get_job_identity",
        lambda jid: {"trace_id": "t1", "repo_slug": "org/repo", "base_branch": "main"},
    )
    monkeypatch.setattr(gh, "get_installation_token", lambda inst_id: "token-123")

    phase_calls = []
    span_calls = []
    monkeypatch.setattr(repo, "set_job_phase", lambda *a: phase_calls.append(a))
    monkeypatch.setattr(repo, "add_span", lambda *a: span_calls.append(a))
    complete_mock = MagicMock()
    monkeypatch.setattr(repo, "complete_job", complete_mock)

    # Mock subprocess run inside process_fix_ci_job
    def _fake_run(cmd, cwd):
        if "checkout" in cmd:
            (cwd / "patch.diff").touch()
        return None

    monkeypatch.setattr(backend_worker, "run", _fake_run)

    # Mock requests.post
    fake_resp = SimpleNamespace(
        status_code=201,
        raise_for_status=lambda: None,
        json=lambda: {"html_url": "https://github.com/org/repo/pull/42"},
    )
    monkeypatch.setattr(backend_worker.requests, "post", lambda *a, **kw: fake_resp)

    job = {
        "job_id": "j1",
        "repo": "org/repo",
        "branch": "main",
        "patch": "diff --git a/src/app.py b/src/app.py\n+fixed\n",
        "run_id": "run-42",
        "installation_id": 999,
    }
    backend_worker.process_fix_ci_job(job)

    complete_mock.assert_called_once()
    args, _ = complete_mock.call_args
    assert args[0] == "j1"
    assert args[1] == "fix-ci/run-42"
    assert args[2] == "https://github.com/org/repo/pull/42"
    assert args[3]["summary"] == "PR opened"


def test_process_fix_ci_job_pytest_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"org/repo"})
    monkeypatch.setattr(backend_worker, "WORKER_TEMP_ROOT", tmp_path / "worker_tmp")
    monkeypatch.setattr(
        repo,
        "get_job_identity",
        lambda jid: {"trace_id": "t1", "repo_slug": "org/repo", "base_branch": "main"},
    )
    monkeypatch.setattr(gh, "get_installation_token", lambda inst_id: "token-123")

    phase_calls = []
    monkeypatch.setattr(repo, "set_job_phase", lambda *a: phase_calls.append(a))
    monkeypatch.setattr(repo, "add_span", MagicMock())

    def _fake_run(cmd, cwd):
        if cmd == ["pytest"]:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return None

    monkeypatch.setattr(backend_worker, "run", _fake_run)

    job = {
        "job_id": "j1",
        "repo": "org/repo",
        "branch": "main",
        "patch": "diff --git a/src/app.py b/src/app.py\n+broken\n",
    }
    backend_worker.process_fix_ci_job(job)

    assert any(call[1] == "failed" and call[2] == "validation_failed" for call in phase_calls)


def test_worker_shutdown_and_loop(monkeypatch) -> None:
    # Test _request_shutdown sets event
    backend_worker._shutdown_event.clear()
    backend_worker._request_shutdown(15, None)
    assert backend_worker._shutdown_event.is_set()

    # Test worker_loop with mocked dequeue
    backend_worker._shutdown_event.clear()
    poll_count = 0

    def _mock_dequeue():
        nonlocal poll_count
        poll_count += 1
        if poll_count == 1:
            return None
        backend_worker._shutdown_event.set()
        return None

    monkeypatch.setattr("worker.backend_worker.dequeue", _mock_dequeue)
    backend_worker.worker_loop()
    assert poll_count >= 1


def test_repository_functions(monkeypatch) -> None:
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("trace-123", "org/repo", "main")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    monkeypatch.setattr("worker.repository.get_conn", lambda: mock_conn)

    # 1. set_job_phase
    repo.set_job_phase("j1", "running", "policy_check", {"repo": "org/repo"}, None)
    assert mock_cursor.execute.called

    # 2. add_span
    repo.add_span("j1", "trace-123", "test_span", "ok", {"key": "val"})
    assert mock_cursor.execute.called

    # 3. get_job_identity
    identity = repo.get_job_identity("j1")
    assert identity == {"trace_id": "trace-123", "repo_slug": "org/repo", "base_branch": "main"}

    # 4. complete_job
    repo.complete_job("j1", "fix-branch", "https://pr.url", {"ok": True})
    assert mock_cursor.execute.called


def test_github_app_client_get_installation_token(monkeypatch) -> None:
    monkeypatch.setattr(
        "worker.github_app_client.create_installation_token", lambda inst_id: f"token-{inst_id}"
    )
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "12345")

    token1 = gh.get_installation_token(555)
    assert token1 == "token-555"

    token2 = gh.get_installation_token(None)
    assert token2 == "token-12345"
