from __future__ import annotations

from pathlib import Path


def test_mission_control_exposes_read_only_orchestrator_evidence_workflow() -> None:
    source = Path("frontend/pages/mission-control.js").read_text()

    assert "ORCHESTRATOR WORKFLOW" in source
    assert "ORCHESTRATOR EVIDENCE" in source
    assert "/orchestrator/runs/${encodeURIComponent(runId)}/events" in source
    assert "/orchestrator/runs/${encodeURIComponent(runId)}/receipts" in source
    assert "Read-only lifecycle, event, receipt, and projection inspection" in source
    assert "start arbitrary job" not in source.lower()
