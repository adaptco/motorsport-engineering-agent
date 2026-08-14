"""V3.8 production-hardening policy and observability helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REQUIRED_OBSERVABILITY_DIMENSIONS = frozenset({"run_id", "agent_id", "lane"})


class ReliabilityPolicyError(ValueError):
    """Raised when V3.8 reliability policy data is incomplete or inconsistent."""


@dataclass(frozen=True)
class ObservabilityContext:
    """Correlation labels required on V3.8 runtime measurements and receipts."""

    run_id: str
    agent_id: str
    lane: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ObservabilityContext:
        missing = sorted(
            name
            for name in REQUIRED_OBSERVABILITY_DIMENSIONS
            if not isinstance(values.get(name), str) or not str(values[name]).strip()
        )
        if missing:
            raise ReliabilityPolicyError(
                f"missing required V3.8 observability dimensions: {', '.join(missing)}"
            )
        return cls(
            run_id=str(values["run_id"]),
            agent_id=str(values["agent_id"]),
            lane=str(values["lane"]),
        )


@dataclass(frozen=True)
class ServiceLevelObjective:
    """An availability target and its corresponding 30-day error budget."""

    service: str
    availability_target_percent: float
    error_budget_percent: float
    error_budget_minutes_30d: float


@dataclass(frozen=True)
class ReliabilityPolicy:
    """Validated V3.8 policy for runtime SLO, rollback, and recovery readiness."""

    schema_version: str
    release: str
    required_dimensions: frozenset[str]
    slos: tuple[ServiceLevelObjective, ...]
    rollback_command: str
    incident_playbook: str


def _policy_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "reliability" / "slo.yaml"


@lru_cache(maxsize=1)
def load_reliability_policy() -> ReliabilityPolicy:
    """Load and validate the repository-owned V3.8 production reliability policy."""

    raw = yaml.safe_load(_policy_path().read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ReliabilityPolicyError("reliability policy must be a YAML mapping")

    schema_version = raw.get("schema_version")
    release = raw.get("release")
    if schema_version != "1.0" or release != "3.8":
        raise ReliabilityPolicyError("reliability policy must target V3.8 schema version 1.0")

    observability = raw.get("observability")
    if not isinstance(observability, dict):
        raise ReliabilityPolicyError("reliability policy must declare observability requirements")
    dimensions = observability.get("required_dimensions")
    if not isinstance(dimensions, list) or set(dimensions) != REQUIRED_OBSERVABILITY_DIMENSIONS:
        expected = ", ".join(sorted(REQUIRED_OBSERVABILITY_DIMENSIONS))
        raise ReliabilityPolicyError(f"required_dimensions must be exactly: {expected}")

    raw_slos = raw.get("service_level_objectives")
    if not isinstance(raw_slos, list) or not raw_slos:
        raise ReliabilityPolicyError(
            "reliability policy must define at least one service-level objective"
        )

    slos: list[ServiceLevelObjective] = []
    for raw_slo in raw_slos:
        if not isinstance(raw_slo, dict):
            raise ReliabilityPolicyError("each service-level objective must be a mapping")
        try:
            service = str(raw_slo["service"])
            target = float(raw_slo["availability_target_percent"])
            error_budget = float(raw_slo["error_budget_percent"])
            budget_minutes = float(raw_slo["error_budget_minutes_30d"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ReliabilityPolicyError(
                "each service-level objective has invalid numeric fields"
            ) from exc
        if not service or not 0 < target < 100:
            raise ReliabilityPolicyError(
                "availability target must be greater than 0 and less than 100"
            )
        if abs((100 - target) - error_budget) > 0.000001:
            raise ReliabilityPolicyError(
                "error budget percent must equal 100 minus availability target"
            )
        expected_minutes = 30 * 24 * 60 * (error_budget / 100)
        if abs(expected_minutes - budget_minutes) > 0.01:
            raise ReliabilityPolicyError(
                "error budget minutes must match the declared 30-day budget"
            )
        slos.append(
            ServiceLevelObjective(
                service=service,
                availability_target_percent=target,
                error_budget_percent=error_budget,
                error_budget_minutes_30d=budget_minutes,
            )
        )

    rollback = raw.get("rollback")
    if not isinstance(rollback, dict):
        raise ReliabilityPolicyError("reliability policy must declare rollback readiness")
    rollback_command = rollback.get("command")
    incident_playbook = rollback.get("incident_playbook")
    if not isinstance(rollback_command, str) or not rollback_command.strip():
        raise ReliabilityPolicyError("rollback command must be declared")
    if not isinstance(incident_playbook, str) or not incident_playbook.strip():
        raise ReliabilityPolicyError("incident playbook must be declared")

    return ReliabilityPolicy(
        schema_version=schema_version,
        release=release,
        required_dimensions=frozenset(dimensions),
        slos=tuple(slos),
        rollback_command=rollback_command,
        incident_playbook=incident_playbook,
    )


def reliability_readiness_snapshot(context: Mapping[str, object]) -> dict[str, Any]:
    """Return a receipt-ready snapshot after enforcing policy and metric context."""

    observability_context = ObservabilityContext.from_mapping(context)
    policy = load_reliability_policy()
    return {
        "release": policy.release,
        "run_id": observability_context.run_id,
        "agent_id": observability_context.agent_id,
        "lane": observability_context.lane,
        "slo_count": len(policy.slos),
        "rollback_command": policy.rollback_command,
        "incident_playbook": policy.incident_playbook,
    }
