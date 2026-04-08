from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path(os.environ.get("A2A_WORKFLOW_STATE_DIR", ".mea_tmp/workflow_state"))
MAX_HISTORY = int(os.environ.get("A2A_WORKFLOW_STATE_MAX_HISTORY", "50"))
DEFAULT_LOOP_SLEEP_SECONDS = float(os.environ.get("A2A_WORKFLOW_LOOP_SLEEP_SECONDS", "0"))

_CHECKBOX_RE = re.compile(r"^\s*-\s*\[(?P<mark>[ xX])\]\s*(?P<label>.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\|\s*(?P<cells>.+?)\s*\|\s*$")
_AC_ROW_RE = re.compile(r"^\|\s*(?P<id>AC-\d+)\s*\|\s*(?P<criterion>.+?)\s*\|")
_WHITESPACE_RE = re.compile(r"\s+")

_MCP_ACCEPTANCE_PATHS: dict[str, list[str]] = {
    "AC-01": ["generation-manifest.json"],
    "AC-02": ["schemas/generation-state.schema.json"],
    "AC-03": ["src/runtime/mcp-v1-runtime.ts"],
    "AC-04": ["Agent.md", "SKILL.md", "tool-registry.json"],
    "AC-05": ["openapi/orchestration-agent.openapi.yaml"],
    "AC-06": ["Agents.md", "registry/agents.registry.json"],
    "AC-07": ["schemas/generation-state.schema.json", "src/runtime/mcp-v1-runtime.ts"],
    "AC-08": ["docs/prd-evaluation.json"],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(session_id: str, workflow_id: str) -> Path:
    safe_session = session_id.replace("/", "_")
    safe_workflow = workflow_id.replace("/", "_")
    return STATE_DIR / f"{safe_session}__{safe_workflow}.json"


def _history_path(session_id: str, workflow_id: str) -> Path:
    safe_session = session_id.replace("/", "_")
    safe_workflow = workflow_id.replace("/", "_")
    return STATE_DIR / "history" / f"{safe_session}__{safe_workflow}.jsonl"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_workflow_state(session_id: str, workflow_id: str) -> dict[str, Any] | None:
    path = _state_path(session_id, workflow_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("session_id") != session_id or data.get("workflow_id") != workflow_id:
        raise ValueError("Persisted workflow state identity mismatch")
    return data


def persist_workflow_state(state: dict[str, Any]) -> dict[str, Any]:
    session_id = str(state["session_id"])
    workflow_id = str(state["workflow_id"])
    path = _state_path(session_id, workflow_id)

    existing = load_workflow_state(session_id, workflow_id)
    version = 1 if not existing else int(existing.get("version", 0)) + 1

    payload = dict(state)
    payload.setdefault("created_at", existing.get("created_at") if existing else _utc_now())
    payload["version"] = version
    payload["updated_at"] = _utc_now()

    _atomic_write(path, payload)
    _append_history(payload)
    _prune_history(session_id, workflow_id)
    return payload


def advance_workflow_position(
    *,
    session_id: str,
    workflow_id: str,
    current_position: str,
    status: str,
    summary: str | None = None,
    pending_actions: list[str] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    trace_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = load_workflow_state(session_id, workflow_id) or {}
    merged = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "run_id": run_id or existing.get("run_id"),
        "trace_id": trace_id or existing.get("trace_id"),
        "current_position": current_position,
        "status": status,
        "summary": summary if summary is not None else existing.get("summary", ""),
        "pending_actions": pending_actions if pending_actions is not None else existing.get("pending_actions", []),
        "artifacts": artifacts if artifacts is not None else existing.get("artifacts", []),
        "metadata": metadata if metadata is not None else existing.get("metadata", {}),
    }
    return persist_workflow_state(merged)


def build_resume_context(session_id: str, workflow_id: str) -> dict[str, Any] | None:
    state = load_workflow_state(session_id, workflow_id)
    if not state:
        return None
    return {
        "session_id": state["session_id"],
        "workflow_id": state["workflow_id"],
        "current_position": state["current_position"],
        "status": state["status"],
        "summary": state.get("summary", ""),
        "pending_actions": state.get("pending_actions", []),
        "artifacts": state.get("artifacts", []),
        "version": state["version"],
        "updated_at": state["updated_at"],
    }


def reconcile_remaining_actions(
    *,
    task_files: list[str | Path],
    task_ledger_path: str | Path | None = None,
    mcp_prd_path: str | Path | None = None,
    completed_acceptance_criteria: list[str] | None = None,
) -> dict[str, Any]:
    remaining_actions: list[str] = []
    completed_criteria = {value.strip() for value in (completed_acceptance_criteria or []) if value.strip()}

    for task_file in task_files:
        path = Path(task_file)
        checklist = _parse_markdown_checklist(path)
        remaining_actions.extend([f"{path.name}: {entry}" for entry in checklist["open"]])

    ledger_open_rows = _parse_task_ledger_open_rows(Path(task_ledger_path)) if task_ledger_path else []
    remaining_actions.extend([f"TASK_LEDGER.md: {entry}" for entry in ledger_open_rows])

    acceptance_criteria = _parse_prd_acceptance_criteria(Path(mcp_prd_path)) if mcp_prd_path else []
    remaining_criteria = [entry for entry in acceptance_criteria if entry["id"] not in completed_criteria]
    remaining_actions.extend([f"MCP PRD {entry['id']}: {entry['criterion']}" for entry in remaining_criteria])

    return {
        "remaining_actions": remaining_actions,
        "remaining_action_count": len(remaining_actions),
        "acceptance_criteria_total": len(acceptance_criteria),
        "acceptance_criteria_remaining": len(remaining_criteria),
    }


def derive_completed_acceptance_criteria(mcp_bundle_root: str | Path) -> list[str]:
    root = Path(mcp_bundle_root)
    checks = {
        "AC-01": _all_exist(root, ["generation-manifest.json"]),
        "AC-02": _all_exist(root, ["schemas/generation-state.schema.json"]),
        "AC-03": _all_exist(root, ["src/runtime/mcp-v1-runtime.ts"]),
        "AC-04": _all_exist(root, ["Agent.md", "SKILL.md", "tool-registry.json"]),
        "AC-05": _all_exist(root, ["openapi/orchestration-agent.openapi.yaml"]),
        "AC-06": _all_exist(root, ["Agents.md", "registry/agents.registry.json"]),
        "AC-07": _looks_checkpoint_aware(root),
        "AC-08": _all_exist(root, ["docs/prd-evaluation.json"]),
    }
    return [criteria for criteria, done in checks.items() if done]


def propose_closure_actions(
    *,
    task_files: list[str | Path],
    task_ledger_path: str | Path,
    mcp_prd_path: str | Path,
    completed_acceptance_criteria: list[str] | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    report = reconcile_remaining_actions(
        task_files=task_files,
        task_ledger_path=task_ledger_path,
        mcp_prd_path=mcp_prd_path,
        completed_acceptance_criteria=completed_acceptance_criteria,
    )
    prioritized = _prioritize_actions(report["remaining_actions"])
    bounded_limit = max(1, limit)
    return prioritized[:bounded_limit]


def derive_completed_acceptance_criteria(mcp_runtime_root: str | Path) -> list[str]:
    root = Path(mcp_runtime_root)
    if not root.exists():
        raise FileNotFoundError(f"MCP runtime root not found: {root}")

    completed: list[str] = []
    for criterion_id, required_paths in _MCP_ACCEPTANCE_PATHS.items():
        if all((root / rel_path).exists() for rel_path in required_paths):
            completed.append(criterion_id)
    return completed


def propose_closure_actions_by_priority(remaining_actions: list[str], limit: int = 10) -> list[dict[str, Any]]:
    normalized_seen: set[str] = set()
    ranked: list[dict[str, Any]] = []

    for action in remaining_actions:
        normalized = _WHITESPACE_RE.sub(" ", action.strip()).lower()
        if not normalized or normalized in normalized_seen:
            continue
        normalized_seen.add(normalized)
        priority = _classify_action_priority(action)
        ranked.append({"priority": priority, "action": action})

    ranked.sort(key=lambda entry: (entry["priority"], entry["action"]))
    bounded = max(1, limit)
    return ranked[:bounded]


def close_checklist_items_with_evidence(
    *,
    checklist_path: str | Path,
    closures: list[dict[str, Any]],
) -> dict[str, int]:
    path = Path(checklist_path)
    if not path.exists():
        raise FileNotFoundError(f"Checklist source not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    closed_count = 0

    for closure in closures:
        contains = str(closure.get("contains", "")).strip()
        evidence = [str(item).strip() for item in closure.get("evidence", []) if str(item).strip()]
        if not contains:
            raise ValueError("closure.contains is required")
        if not evidence:
            raise ValueError(f"Evidence is required to close checklist item: {contains}")
        for evidence_path in evidence:
            if not Path(evidence_path).exists():
                raise FileNotFoundError(f"Evidence path does not exist: {evidence_path}")

        for index, line in enumerate(lines):
            if not line.lstrip().startswith("- [ ] "):
                continue
            if contains not in line:
                continue
            lines[index] = (
                line.replace("- [ ] ", "- [x] ", 1)
                + f" (Evidence: {', '.join(evidence)})"
            )
            closed_count += 1
            break

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"closed": closed_count, "requested": len(closures)}


def run_task_reconciliation_loop(
    *,
    session_id: str,
    workflow_id: str,
    task_files: list[str | Path],
    task_ledger_path: str | Path,
    mcp_prd_path: str | Path | None = None,
    completed_acceptance_criteria: list[str] | None = None,
    max_iterations: int = 25,
    sleep_seconds: float = DEFAULT_LOOP_SLEEP_SECONDS,
    run_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    bounded_iterations = max(1, max_iterations)
    bounded_sleep = max(0.0, sleep_seconds)
    latest_state: dict[str, Any] | None = None

    for iteration in range(1, bounded_iterations + 1):
        report = reconcile_remaining_actions(
            task_files=task_files,
            task_ledger_path=task_ledger_path,
            mcp_prd_path=mcp_prd_path,
            completed_acceptance_criteria=completed_acceptance_criteria,
        )
        pending_actions = report["remaining_actions"]
        done = not pending_actions
        status = "complete" if done else "running"
        summary = (
            "All tracked task actions and PRD acceptance criteria are complete."
            if done
            else f"{len(pending_actions)} actions remain after reconciliation iteration {iteration}."
        )

        latest_state = advance_workflow_position(
            session_id=session_id,
            workflow_id=workflow_id,
            current_position="task-reconciliation",
            status=status,
            summary=summary,
            pending_actions=pending_actions,
            run_id=run_id,
            trace_id=trace_id,
            metadata={
                "loop_iteration": iteration,
                "loop_max_iterations": bounded_iterations,
                "remaining_action_count": report["remaining_action_count"],
                "acceptance_criteria_total": report["acceptance_criteria_total"],
                "acceptance_criteria_remaining": report["acceptance_criteria_remaining"],
            },
        )
        if done:
            return latest_state
        if iteration < bounded_iterations and bounded_sleep > 0:
            time.sleep(bounded_sleep)

    assert latest_state is not None  # bounded_iterations ensures at least one pass
    if latest_state.get("status") != "complete":
        latest_state = advance_workflow_position(
            session_id=session_id,
            workflow_id=workflow_id,
            current_position="task-reconciliation",
            status="blocked",
            summary=(
                f"Task reconciliation loop reached max iterations ({bounded_iterations}) before completion."
            ),
            pending_actions=list(latest_state.get("pending_actions", [])),
            run_id=run_id or latest_state.get("run_id"),
            trace_id=trace_id or latest_state.get("trace_id"),
            metadata={
                **dict(latest_state.get("metadata", {})),
                "blocked_reason": "max_iterations_exhausted",
            },
        )
    return latest_state


def _append_history(payload: dict[str, Any]) -> None:
    path = _history_path(str(payload["session_id"]), str(payload["workflow_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _prune_history(session_id: str, workflow_id: str) -> None:
    path = _history_path(session_id, workflow_id)
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= MAX_HISTORY:
        return
    kept = lines[-MAX_HISTORY:]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def _parse_markdown_checklist(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Checklist source not found: {path}")
    open_items: list[str] = []
    closed_items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _CHECKBOX_RE.match(line)
        if not match:
            continue
        label = match.group("label").strip()
        if match.group("mark").strip().lower() == "x":
            closed_items.append(label)
        else:
            open_items.append(label)
    return {"open": open_items, "closed": closed_items}


def _parse_task_ledger_open_rows(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Task ledger not found: {path}")
    open_rows: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _TABLE_ROW_RE.match(line)
        if not match:
            continue
        cells = [cell.strip() for cell in match.group("cells").split("|")]
        if len(cells) < 2:
            continue
        task_name = cells[0]
        status = cells[1]
        if task_name.lower() == "task" or set(task_name) == {"-"}:
            continue
        normalized = status.lower()
        if "open" in normalized or "⚪" in normalized:
            open_rows.append(task_name)
    return open_rows


def _parse_prd_acceptance_criteria(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"MCP PRD not found: {path}")
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _AC_ROW_RE.match(line)
        if not match:
            continue
        rows.append({"id": match.group("id"), "criterion": match.group("criterion").strip()})
    return rows


def _all_exist(root: Path, relative_paths: list[str]) -> bool:
    return all((root / relative_path).exists() for relative_path in relative_paths)


def _looks_checkpoint_aware(root: Path) -> bool:
    runtime_module = root / "src" / "runtime" / "mcp-v1-runtime.ts"
    state_schema = root / "schemas" / "generation-state.schema.json"
    if not runtime_module.exists() or not state_schema.exists():
        return False
    module_text = runtime_module.read_text(encoding="utf-8").lower()
    schema_text = state_schema.read_text(encoding="utf-8").lower()
    return "checkpoint" in module_text and "checkpoint" in schema_text


def _prioritize_actions(actions: list[str]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for action in actions:
        normalized = action.lower()
        priority = "P2"
        if action.startswith("TASK_LEDGER.md:"):
            priority = "P0"
        if action.startswith("MCP PRD AC-"):
            priority = "P0"
        if any(token in normalized for token in ["critical", "blocker", "must fix", "phase 1", "p1"]):
            priority = "P1" if priority != "P0" else "P0"
        if any(token in normalized for token in ["phase 2", "phase 3", "nice to have", "optional"]):
            priority = "P2"
        rank = {"P0": 0, "P1": 1, "P2": 2}[priority]
        ranked.append({"priority": priority, "action": action, "rank": rank})
    ranked.sort(key=lambda entry: (entry["rank"], entry["action"]))
    for idx, entry in enumerate(ranked, start=1):
        entry["order"] = idx
        entry.pop("rank", None)
    return ranked


def _classify_action_priority(action: str) -> int:
    probe = action.lower()
    if any(token in probe for token in ("critical", "blocker", "🔴", " p0 ", "p0:")):
        return 0
    if any(token in probe for token in ("p1", "missing", "deploy", "forensic", "rate limit", "circuit breaker")):
        return 1
    if any(token in probe for token in ("p2", "quality", "documentation", "runbook", "lint", "mypy")):
        return 2
    return 3
