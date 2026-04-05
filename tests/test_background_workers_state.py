from __future__ import annotations

from pathlib import Path

from worker import background_workers as bg


def test_persist_and_resume_workflow_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bg, "STATE_DIR", tmp_path)
    monkeypatch.setattr(bg, "MAX_HISTORY", 5)

    saved = bg.advance_workflow_position(
        session_id="sess-1",
        workflow_id="release-gate",
        current_position="version-alignment",
        status="running",
        summary="validating changelog and version manifest",
        pending_actions=["wait test", "wait build-images"],
        artifacts=[{"kind": "file", "ref": ".github/workflows/release-gate.yml"}],
        run_id="run-123",
        trace_id="trace-123",
    )

    assert saved["version"] == 1
    assert saved["current_position"] == "version-alignment"
    assert saved["status"] == "running"

    resumed = bg.build_resume_context("sess-1", "release-gate")
    assert resumed is not None
    assert resumed["current_position"] == "version-alignment"
    assert resumed["pending_actions"] == ["wait test", "wait build-images"]

    next_saved = bg.advance_workflow_position(
        session_id="sess-1",
        workflow_id="release-gate",
        current_position="required-ci-checks",
        status="blocked",
    )
    assert next_saved["version"] == 2
    assert next_saved["current_position"] == "required-ci-checks"


def test_history_is_pruned(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bg, "STATE_DIR", tmp_path)
    monkeypatch.setattr(bg, "MAX_HISTORY", 3)

    for index in range(5):
        bg.advance_workflow_position(
            session_id="sess-2",
            workflow_id="mea-kernel-ci",
            current_position=f"step-{index}",
            status="running",
        )

    history_path = tmp_path / "history" / "sess-2__mea-kernel-ci.jsonl"
    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert '"current_position": "step-4"' in lines[-1]
