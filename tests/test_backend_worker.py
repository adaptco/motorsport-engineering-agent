from pathlib import Path

import worker.backend_worker as backend_worker


def test_process_fix_ci_job_validation_success(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []
    phases: list[tuple] = []
    posts: list[str] = []

    class _TempDir:
        def __enter__(self) -> str:
            return str(tmp_path)

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"org/repo"})
    monkeypatch.setattr(backend_worker, "get_job_identity", lambda _job_id: {"trace_id": "trace-1"})
    monkeypatch.setattr(backend_worker, "get_installation_token", lambda _installation_id: "token")
    monkeypatch.setattr(backend_worker, "tempfile", type("T", (), {"TemporaryDirectory": _TempDir}))
    monkeypatch.setattr(backend_worker, "add_span", lambda *args, **kwargs: None)
    monkeypatch.setattr(backend_worker, "set_job_phase", lambda *args, **kwargs: phases.append((args, kwargs)))
    monkeypatch.setattr(backend_worker, "complete_job", lambda *args, **kwargs: None)

    def _run(cmd: list[str], cwd: Path) -> None:
        assert cwd == tmp_path
        commands.append(cmd)

    monkeypatch.setattr(backend_worker, "run", _run)
    monkeypatch.setattr(
        backend_worker,
        "create_pull_request",
        lambda **_kwargs: (posts.append("pr"), "https://example.com/pr/1")[1],
    )

    backend_worker.process_fix_ci_job(
        {
            "job_id": "job-1",
            "repo": "org/repo",
            "branch": "main",
            "patch": "diff --git a/a b/a\n",
            "run_id": "run-1",
        }
    )

    assert ["pytest"] in commands
    assert any(cmd[:3] == ["git", "commit", "-m"] for cmd in commands)
    assert any(cmd[:3] == ["git", "push", "origin"] for cmd in commands)
    assert len(posts) == 1
    assert any(args[1:3] == ("running", "validated") for args, _kwargs in phases)


def test_process_fix_ci_job_missing_default_pytest_skips_validation(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []
    phases: list[tuple] = []
    posts: list[str] = []

    class _TempDir:
        def __enter__(self) -> str:
            return str(tmp_path)

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"org/repo"})
    monkeypatch.setattr(backend_worker, "get_job_identity", lambda _job_id: {"trace_id": "trace-1"})
    monkeypatch.setattr(backend_worker, "get_installation_token", lambda _installation_id: "token")
    monkeypatch.setattr(backend_worker, "tempfile", type("T", (), {"TemporaryDirectory": _TempDir}))
    monkeypatch.setattr(backend_worker, "add_span", lambda *args, **kwargs: None)
    monkeypatch.setattr(backend_worker, "set_job_phase", lambda *args, **kwargs: phases.append((args, kwargs)))
    monkeypatch.setattr(backend_worker, "complete_job", lambda *args, **kwargs: None)

    def _run(cmd: list[str], cwd: Path) -> None:
        assert cwd == tmp_path
        commands.append(cmd)
        if cmd == ["pytest"]:
            raise FileNotFoundError("pytest not found")

    monkeypatch.setattr(backend_worker, "run", _run)
    monkeypatch.setattr(
        backend_worker,
        "create_pull_request",
        lambda **_kwargs: (posts.append("pr"), "https://example.com/pr/1")[1],
    )

    backend_worker.process_fix_ci_job(
        {
            "job_id": "job-2",
            "repo": "org/repo",
            "branch": "main",
            "patch": "diff --git a/a b/a\n",
            "run_id": "run-2",
        }
    )

    assert ["pytest"] in commands
    assert any(cmd[:3] == ["git", "commit", "-m"] for cmd in commands)
    assert any(cmd[:3] == ["git", "push", "origin"] for cmd in commands)
    assert len(posts) == 1
    assert any(args[1:3] == ("running", "validation_skipped") for args, _kwargs in phases)


def test_process_fix_ci_job_missing_custom_validation_cmd_fails_closed(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []
    phases: list[tuple] = []

    class _TempDir:
        def __enter__(self) -> str:
            return str(tmp_path)

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"org/repo"})
    monkeypatch.setattr(backend_worker, "VALIDATION_CMD", "my-test-runner")
    monkeypatch.setattr(backend_worker, "get_job_identity", lambda _job_id: {"trace_id": "trace-1"})
    monkeypatch.setattr(backend_worker, "get_installation_token", lambda _installation_id: "token")
    monkeypatch.setattr(backend_worker, "tempfile", type("T", (), {"TemporaryDirectory": _TempDir}))
    monkeypatch.setattr(backend_worker, "add_span", lambda *args, **kwargs: None)
    monkeypatch.setattr(backend_worker, "set_job_phase", lambda *args, **kwargs: phases.append((args, kwargs)))
    monkeypatch.setattr(backend_worker, "complete_job", lambda *args, **kwargs: None)

    def _run(cmd: list[str], cwd: Path) -> None:
        assert cwd == tmp_path
        commands.append(cmd)
        if cmd == ["my-test-runner"]:
            raise FileNotFoundError("my-test-runner not found")

    monkeypatch.setattr(backend_worker, "run", _run)
    monkeypatch.setattr(backend_worker, "create_pull_request", lambda **_kwargs: "https://example.com/pr/1")

    backend_worker.process_fix_ci_job(
        {
            "job_id": "job-3",
            "repo": "org/repo",
            "branch": "main",
            "patch": "diff --git a/a b/a\n",
            "run_id": "run-3",
        }
    )

    assert ["my-test-runner"] in commands
    assert not any(cmd[:3] == ["git", "commit", "-m"] for cmd in commands)
    assert not any(cmd[:3] == ["git", "push", "origin"] for cmd in commands)
    assert any(args[1:3] == ("failed", "validation_failed") for args, _kwargs in phases)
