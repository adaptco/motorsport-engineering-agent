"""External HTTP integration coverage for the V3.8 Docker Compose runtime."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest

RUN_LIVE_STACK_TESTS = os.environ.get("MEA_RUN_INTEGRATION_TESTS") == "1"
CONTROL_PLANE_URL = os.environ.get("MEA_CONTROL_PLANE_URL", "http://127.0.0.1:8000").rstrip("/")
MCP_SERVER_URL = os.environ.get("MEA_MCP_SERVER_URL", "http://127.0.0.1:7000").rstrip("/")
NORMALIZED_OUTPUT_DIR = Path(os.environ.get("MEA_INTEGRATION_HOST_OUTPUT_DIR", ".mea_tmp/live"))
MCP_TOKEN = os.environ.get("MCP_SHARED_BEARER_TOKEN", "").strip()

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_STACK_TESTS,
    reason="requires MEA_RUN_INTEGRATION_TESTS=1 and a running Docker Compose V3.8 stack",
)


def _assert_ok(response: httpx.Response) -> dict:
    assert response.status_code == 200, response.text
    return response.json()


def _mcp_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else {}


def test_live_stack_health_telemetry_ingest_and_replay_lifecycle() -> None:
    with httpx.Client(timeout=20.0) as client:
        control_health = _assert_ok(client.get(f"{CONTROL_PLANE_URL}/healthz"))
        assert control_health == {
            "status": "ok",
            "kernel_version": "3.8",
            "package_version": "0.3.8",
        }

        mcp_health = _assert_ok(client.get(f"{MCP_SERVER_URL}/healthz"))
        assert mcp_health == control_health

        normalized = _assert_ok(
            client.post(
                f"{CONTROL_PLANE_URL}/ingest/normalize",
                json={
                    "input_path": "/integration-fixtures/sample_export.csv",
                    "output_dir": "/integration-output",
                    "vendor_hint": "csv_export",
                    "session_id": "live-stack-telemetry",
                },
            )
        )
        assert normalized["status"] == "complete"
        assert normalized["row_count"] > 0
        normalized_csv = NORMALIZED_OUTPUT_DIR / Path(normalized["normalized_csv"]).name
        assert normalized_csv.exists()

        parsed = _assert_ok(
            client.post(
                f"{CONTROL_PLANE_URL}/runtime/logs/parse",
                files={
                    "file": (
                        "live-stack-telemetry.csv",
                        normalized_csv.read_bytes(),
                        "text/csv",
                    )
                },
            )
        )
        session_id = parsed["summary"]["session_id"]
        assert parsed["summary"]["rows"] == normalized["row_count"]

        sessions = _assert_ok(client.get(f"{CONTROL_PLANE_URL}/runtime/sessions"))
        assert any(item["session_id"] == session_id for item in sessions)

        debrief = _assert_ok(
            client.get(f"{CONTROL_PLANE_URL}/runtime/sessions/{session_id}/debrief")
        )
        assert debrief["session_id"] == session_id
        assert debrief["row_count"] == normalized["row_count"]

        replay = _assert_ok(
            client.post(
                f"{CONTROL_PLANE_URL}/session/replay",
                json={
                    "artifact_path": "/integration-fixtures/live_stack_telemetry.jsonl",
                    "sampling_hz": 60,
                    "source": "jsonl",
                    "strict": True,
                },
            )
        )
        assert replay["status"] == "complete"
        assert replay["metrics"]["frames_valid"] == 3
        assert all(task["status"] == "pass" for task in replay["tasks"])


def test_live_stack_mcp_contract_and_agent_handoff_state() -> None:
    headers = _mcp_headers()
    handoff_session = "live-stack-v38-handoff"
    with httpx.Client(timeout=20.0) as client:
        info = _assert_ok(client.get(f"{MCP_SERVER_URL}/mcp/info", headers=headers))
        assert info["runtime_id"] == "motorsport-engineering-agent-mcp"
        assert info["version"] == "3.8"
        assert info["package_version"] == "0.3.8"
        assert info["agent_count"] == 5

        agents = _assert_ok(client.get(f"{MCP_SERVER_URL}/mcp/agents", headers=headers))
        assert {agent["agent_id"] for agent in agents} == {
            "planner",
            "researcher",
            "coder",
            "reviewer",
            "tester",
        }

        invocation = _assert_ok(
            client.post(
                f"{MCP_SERVER_URL}/mcp/invoke",
                headers=headers,
                json={
                    "agent_id": "planner",
                    "capability": "plan",
                    "arguments": {"objective": "validate V3.8 telemetry replay"},
                    "resource_uri": "repo://PRD.md",
                },
            )
        )
        assert invocation["status"] == "queued"
        assert invocation["agent_id"] == "planner"
        assert invocation["capability"] == "plan"

        tool_result = _assert_ok(
            client.post(
                f"{MCP_SERVER_URL}/tools/call",
                headers=headers,
                json={
                    "name": "mea_ci_guardrail",
                    "arguments": {
                        "ci_state": "green",
                        "proposed_patch": "+++ tests/integration/test_live_stack_v38.py\\n",
                    },
                },
            )
        )
        assert tool_result["safe_action"] == "emit_patch"
        assert tool_result["uncertain"] is False

        events = (
            {
                "idempotency_key": "live-stack-planner",
                "session_id": handoff_session,
                "event_type": "agent_upsert",
                "payload": {
                    "agent_id": "planner",
                    "display_name": "Planner",
                    "runtime": "worktree",
                    "branch": "main",
                    "commit_hash": "8c28263",
                    "note": "telemetry analysis planned",
                },
            },
            {
                "idempotency_key": "live-stack-task",
                "session_id": handoff_session,
                "event_type": "task_upsert",
                "payload": {
                    "task_id": "telemetry-replay",
                    "title": "Validate telemetry replay",
                    "state": "running",
                    "assigned_agent": "coder",
                    "source": "planner-handoff",
                },
            },
            {
                "idempotency_key": "live-stack-coder",
                "session_id": handoff_session,
                "event_type": "agent_upsert",
                "payload": {
                    "agent_id": "coder",
                    "display_name": "Coder",
                    "runtime": "worktree",
                    "branch": "main",
                    "commit_hash": "8c28263",
                    "note": "telemetry replay handoff accepted",
                },
            },
        )
        for event in events:
            receipt = _assert_ok(
                client.post(f"{MCP_SERVER_URL}/runtime-state/events", headers=headers, json=event)
            )
            assert receipt["status"] == "accepted"

        snapshot = _assert_ok(
            client.get(
                f"{MCP_SERVER_URL}/runtime-state/snapshot",
                headers=headers,
                params={"session_id": handoff_session},
            )
        )
        assert snapshot["last_seq"] == 3
        assert snapshot["agents"]["planner"]["branch"] == "main"
        assert snapshot["agents"]["coder"]["branch"] == "main"
        assert snapshot["tasks"]["telemetry-replay"]["assigned_agent"] == "coder"

        replayed_events = _assert_ok(
            client.get(
                f"{MCP_SERVER_URL}/runtime-state/events",
                headers=headers,
                params={"session_id": handoff_session, "after_seq": 1},
            )
        )
        assert [event["seq"] for event in replayed_events["events"]] == [2, 3]
