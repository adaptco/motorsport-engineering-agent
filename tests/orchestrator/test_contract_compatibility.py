from __future__ import annotations

import json
from pathlib import Path

from services.orchestrator.domain.models import ExecutionState


def test_existing_contract_authorities_remain_available_and_unchanged_in_role() -> None:
    runtime_contract = json.loads(
        Path("contracts/runtime/agent_runtime_contract_bundle.schema.json").read_text()
    )
    execution_control = json.loads(
        Path("contracts/runtime/execution-control.schema.json").read_text()
    )
    orchestrator_run = json.loads(
        Path("contracts/orchestrator/orchestrator_run.schema.json").read_text()
    )

    assert runtime_contract["title"] == "MEA Agent Runtime Contract Bundle"
    assert execution_control["title"] == "MEA Execution Control Contract"
    assert set(
        execution_control["$defs"]["ExecutionCommand"]["properties"]["command_type"]["enum"]
    ) == {
        "SCHEDULE",
        "CANCEL",
        "PAUSE",
        "RESUME",
        "CHECKPOINT",
    }
    assert orchestrator_run["title"] == "Orchestrator Run"
    assert "governance" in orchestrator_run["properties"]


def test_gate_three_lifecycle_is_an_additive_internal_projection() -> None:
    assert ExecutionState.REQUESTED.value == "requested"
    assert ExecutionState.ATTEMPT_CREATED.value == "attempt_created"
    assert ExecutionState.LEASED.value == "leased"
    assert ExecutionState.COMPLETED.value == "completed"
