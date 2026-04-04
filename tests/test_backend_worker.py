import subprocess

from worker import backend_worker


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _job():
    return {
        "job_id": "job-1",
        "repo": "acme/repo",
        "branch": "main",
        "patch": "diff --git a/README.md b/README.md\nindex e69de29..4b825dc 100644\n--- a/README.md\n+++ b/README.md\n@@ -0,0 +1 @@\n+test\n",
        "installation_id": 123,
        "run_id": "run-42",
    }


def test_process_fix_ci_job_marks_validation_failed_and_returns_early(monkeypatch):
    calls = {"phases": [], "spans": [], "run": [], "complete": [], "post": []}

    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"acme/repo"})
    monkeypatch.setattr(backend_worker, "get_job_identity", lambda job_id: {"trace_id": "trace-1"})
    monkeypatch.setattr(backend_worker, "get_installation_token", lambda installation_id: "token")
    monkeypatch.setattr(
        backend_worker,
        "set_job_phase",
        lambda *args, **kwargs: calls["phases"].append((args, kwargs)),
    )
    monkeypatch.setattr(
        backend_worker,
        "add_span",
        lambda *args, **kwargs: calls["spans"].append((args, kwargs)),
    )
    monkeypatch.setattr(
        backend_worker,
        "complete_job",
        lambda *args, **kwargs: calls["complete"].append((args, kwargs)),
    )

    def fake_run(cmd, cwd):
        calls["run"].append(cmd)
        if cmd == ["pytest"]:
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(backend_worker, "run", fake_run)
    monkeypatch.setattr(
        backend_worker.requests,
        "post",
        lambda *args, **kwargs: calls["post"].append((args, kwargs)),
    )

    backend_worker.process_fix_ci_job(_job())

    assert any(args[1] == "failed" and args[2] == "validation_failed" for args, _ in calls["phases"])
    assert not calls["complete"]
    assert not calls["post"]
    assert ["git", "commit", "-m", "Fix CI run run-42"] not in calls["run"]
    assert ["git", "push", "origin", "fix-ci/run-42"] not in calls["run"]


def test_process_fix_ci_job_completes_when_validation_passes(monkeypatch):
    calls = {"phases": [], "complete": []}

    monkeypatch.setattr(backend_worker, "ALLOWED_REPOS", {"acme/repo"})
    monkeypatch.setattr(backend_worker, "get_job_identity", lambda job_id: {"trace_id": "trace-1"})
    monkeypatch.setattr(backend_worker, "get_installation_token", lambda installation_id: "token")
    monkeypatch.setattr(backend_worker, "add_span", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        backend_worker,
        "set_job_phase",
        lambda *args, **kwargs: calls["phases"].append((args, kwargs)),
    )
    monkeypatch.setattr(
        backend_worker,
        "complete_job",
        lambda *args, **kwargs: calls["complete"].append((args, kwargs)),
    )
    monkeypatch.setattr(backend_worker, "run", lambda cmd, cwd: None)
    monkeypatch.setattr(
        backend_worker.requests,
        "post",
        lambda *args, **kwargs: _FakeResponse({"html_url": "https://example.test/pr/1"}),
    )

    backend_worker.process_fix_ci_job(_job())

    assert calls["complete"]
    assert not any(args[1] == "failed" and args[2] == "validation_failed" for args, _ in calls["phases"])
