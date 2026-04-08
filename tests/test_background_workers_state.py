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


def test_reconcile_remaining_actions_parses_task_and_prd_sources(tmp_path: Path) -> None:
    task_file = tmp_path / "TASK-004.md"
    task_file.write_text(
        "\n".join(
            [
                "# Task",
                "- [x] done item",
                "- [ ] open item",
            ]
        ),
        encoding="utf-8",
    )
    ledger_file = tmp_path / "TASK_LEDGER.md"
    ledger_file.write_text(
        "\n".join(
            [
                "| Task | Status |",
                "| --- | --- |",
                "| Closed work | 🟢 Done |",
                "| Open work | ⚪ Open |",
            ]
        ),
        encoding="utf-8",
    )
    prd_file = tmp_path / "PRD.md"
    prd_file.write_text(
        "\n".join(
            [
                "| ID | Criterion | Pass condition |",
                "| --- | --- | --- |",
                "| AC-01 | Manifest exists | pass |",
                "| AC-02 | State schema exists | pass |",
            ]
        ),
        encoding="utf-8",
    )

    report = bg.reconcile_remaining_actions(
        task_files=[task_file],
        task_ledger_path=ledger_file,
        mcp_prd_path=prd_file,
        completed_acceptance_criteria=["AC-02"],
    )

    assert report["remaining_action_count"] == 3
    assert "TASK-004.md: open item" in report["remaining_actions"]
    assert "TASK_LEDGER.md: Open work" in report["remaining_actions"]
    assert "MCP PRD AC-01: Manifest exists" in report["remaining_actions"]


def test_run_task_reconciliation_loop_blocks_after_max_iterations(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bg, "STATE_DIR", tmp_path)
    monkeypatch.setattr(bg, "MAX_HISTORY", 10)

    task_file = tmp_path / "TASK-005.md"
    task_file.write_text("- [ ] unresolved documentation item\n", encoding="utf-8")
    ledger_file = tmp_path / "TASK_LEDGER.md"
    ledger_file.write_text(
        "\n".join(
            [
                "| Task | Status |",
                "| --- | --- |",
                "| Remaining task | ⚪ Open |",
            ]
        ),
        encoding="utf-8",
    )
    prd_file = tmp_path / "PRD.md"
    prd_file.write_text(
        "\n".join(
            [
                "| ID | Criterion | Pass condition |",
                "| --- | --- | --- |",
                "| AC-01 | Manifest exists | pass |",
            ]
        ),
        encoding="utf-8",
    )

    state = bg.run_task_reconciliation_loop(
        session_id="sess-loop",
        workflow_id="ralph-loop",
        task_files=[task_file],
        task_ledger_path=ledger_file,
        mcp_prd_path=prd_file,
        completed_acceptance_criteria=[],
        max_iterations=1,
        sleep_seconds=0,
    )

    assert state["status"] == "blocked"
    assert state["metadata"]["blocked_reason"] == "max_iterations_exhausted"
    assert len(state["pending_actions"]) == 3
