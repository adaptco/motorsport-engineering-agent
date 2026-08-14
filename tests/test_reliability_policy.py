"""Regression tests for V3.8 production-hardening policy."""

from __future__ import annotations

import pytest

from shared.reliability import (
    REQUIRED_OBSERVABILITY_DIMENSIONS,
    ReliabilityPolicyError,
    load_reliability_policy,
    reliability_readiness_snapshot,
)


def test_v38_reliability_policy_declares_slos_and_rollback_readiness() -> None:
    policy = load_reliability_policy()

    assert policy.release == "3.8"
    assert policy.required_dimensions == REQUIRED_OBSERVABILITY_DIMENSIONS
    assert {slo.service for slo in policy.slos} == {
        "control-plane",
        "mcp-server",
        "backend-worker",
    }
    assert policy.rollback_command == "./deploy/rollback.sh <backup_directory>"
    assert policy.incident_playbook == "docs/ops/V3_8_PRODUCTION_READINESS.md"


def test_reliability_snapshot_requires_all_observability_dimensions() -> None:
    snapshot = reliability_readiness_snapshot(
        {"run_id": "run-123", "agent_id": "agent-orchestrator", "lane": "orch"}
    )

    assert snapshot["release"] == "3.8"
    assert snapshot["slo_count"] == 3
    assert snapshot["lane"] == "orch"


@pytest.mark.parametrize(
    "context",
    [
        {"agent_id": "agent-orchestrator", "lane": "orch"},
        {"run_id": "run-123", "lane": "orch"},
        {"run_id": "run-123", "agent_id": "agent-orchestrator"},
        {"run_id": "run-123", "agent_id": "", "lane": "orch"},
    ],
)
def test_reliability_snapshot_rejects_incomplete_observability_context(
    context: dict[str, str],
) -> None:
    with pytest.raises(ReliabilityPolicyError, match="observability dimensions"):
        reliability_readiness_snapshot(context)
