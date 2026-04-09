import json
from pathlib import Path


def test_event_order_exists():
    """Ensure that the event ordering for the runtime harness is defined."""
    schema_path = Path(__file__).resolve().parents[1] / "contracts/runtime/agent_runtime_contract_bundle.schema.json"
    with schema_path.open() as f:
        schema = json.load(f)

    events = [
        "request.received",
        "run.created",
        "workflow.policy.screened",
        "plan.proposed",
        "step.dispatched",
        "approval.resolved",
        "tool.requested",
        "tool.executed",
        "action.proposed",
        "state.transitioned",
        "checkpoint.persisted",
        "run.completed",
        "run.failed",
        "audit.bundle.written",
    ]

    defined_events = set()
    for definition in schema.get("$defs", {}).values():
        if not isinstance(definition, dict):
            continue

        # Check direct properties
        event_type = definition.get("properties", {}).get("event_type", {}).get("const")
        if event_type:
            defined_events.add(event_type)
            continue

        # Check allOf
        for item in definition.get("allOf", []):
            if isinstance(item, dict):
                event_type = item.get("properties", {}).get("event_type", {}).get("const")
                if event_type:
                    defined_events.add(event_type)
                    break

    for event in events:
        assert event in defined_events, f"Event '{event}' not found in schema"
