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


def test_derive_completed_acceptance_criteria(tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir(parents=True)
    (tmp_path / "src" / "runtime").mkdir(parents=True)
    (tmp_path / "openapi").mkdir(parents=True)
    (tmp_path / "registry").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)

    (tmp_path / "generation-manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "schemas" / "generation-state.schema.json").write_text('{"checkpoint":{}}', encoding="utf-8")
    (tmp_path / "src" / "runtime" / "mcp-v1-runtime.ts").write_text("// checkpoint model", encoding="utf-8")
    (tmp_path / "Agent.md").write_text("# Agent", encoding="utf-8")
    (tmp_path / "SKILL.md").write_text("# Skill", encoding="utf-8")
    (tmp_path / "tool-registry.json").write_text("{}", encoding="utf-8")
    (tmp_path / "openapi" / "orchestration-agent.openapi.yaml").write_text("openapi: 3.0.0", encoding="utf-8")
    (tmp_path / "Agents.md").write_text("# Agents", encoding="utf-8")
    (tmp_path / "registry" / "agents.registry.json").write_text("{}", encoding="utf-8")
    (tmp_path / "docs" / "prd-evaluation.json").write_text("{}", encoding="utf-8")

    completed = bg.derive_completed_acceptance_criteria(tmp_path)
    assert completed == ["AC-01", "AC-02", "AC-03", "AC-04", "AC-05", "AC-06", "AC-07", "AC-08"]


def test_propose_closure_actions_prioritizes_ledger_and_prd(tmp_path: Path) -> None:
    task_file = tmp_path / "TASK-007.md"
    task_file.write_text("- [ ] critical runtime blocker\n- [ ] optional cleanup\n", encoding="utf-8")
    ledger_file = tmp_path / "TASK_LEDGER.md"
    ledger_file.write_text(
        "\n".join(
            [
                "| Task | Status |",
                "| --- | --- |",
                "| P1 hardening | ⚪ Open |",
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

    actions = bg.propose_closure_actions(
        task_files=[task_file],
        task_ledger_path=ledger_file,
        mcp_prd_path=prd_file,
        completed_acceptance_criteria=[],
        limit=10,
    )
    assert actions[0]["priority"] == "P0"
    assert actions[0]["action"].startswith("MCP PRD AC-01:")
    assert any(item["priority"] == "P1" for item in actions)


def test_derive_completed_acceptance_criteria(tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "runtime").mkdir(parents=True, exist_ok=True)
    (tmp_path / "openapi").mkdir(parents=True, exist_ok=True)
    (tmp_path / "registry").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)

    for rel_path in [
        "generation-manifest.json",
        "schemas/generation-state.schema.json",
        "src/runtime/mcp-v1-runtime.ts",
        "Agent.md",
        "SKILL.md",
        "tool-registry.json",
        "openapi/orchestration-agent.openapi.yaml",
        "Agents.md",
        "registry/agents.registry.json",
    ]:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    completed = bg.derive_completed_acceptance_criteria(tmp_path)
    assert "AC-01" in completed
    assert "AC-07" in completed
    assert "AC-08" not in completed


def test_propose_closure_actions_by_priority_sorts_and_deduplicates() -> None:
    actions = [
        "Task A critical blocker",
        "Task B p2 docs",
        "Task A   critical blocker",
        "Task C misc",
    ]
    ranked = bg.propose_closure_actions_by_priority(actions, limit=3)
    assert ranked[0]["action"] == "Task A critical blocker"
    assert ranked[0]["priority"] == 0
    assert len(ranked) == 3


def test_close_checklist_items_with_evidence(tmp_path: Path) -> None:
    checklist = tmp_path / "TASK.md"
    checklist.write_text("- [ ] create docs\n- [ ] add test\n", encoding="utf-8")
    evidence = tmp_path / "docs.md"
    evidence.write_text("ok\n", encoding="utf-8")

    result = bg.close_checklist_items_with_evidence(
        checklist_path=checklist,
        closures=[{"contains": "create docs", "evidence": [str(evidence)]}],
    )

    assert result["closed"] == 1
    output = checklist.read_text(encoding="utf-8")
    assert "- [x] create docs" in output
    assert "(Evidence:" in output


def test_close_checklist_items_requires_evidence(tmp_path: Path) -> None:
    checklist = tmp_path / "TASK.md"
    checklist.write_text("- [ ] create docs\n", encoding="utf-8")
    try:
        bg.close_checklist_items_with_evidence(
            checklist_path=checklist,
            closures=[{"contains": "create docs", "evidence": []}],
        )
        assert False, "expected ValueError for missing evidence"
    except ValueError as exc:
        assert "Evidence is required" in str(exc)
