---
name: a2a-mcp-agent-env-map
description: Build and maintain a fail-closed environment-variable and runtime contract map for Motorsport Engineering Agent (MEA) across control plane, worker, MCP server, and GitHub integration paths. Use when auditing env drift, wiring deployments, or documenting startup contracts.
---

# a2a-mcp-agent-env-map

## Purpose
Create an auditable map of MEA environment contracts and integration boundaries, with explicit fail-closed gates.

## When to use
- User asks for environment mapping, runtime contract validation, or deployment wiring checks.
- User asks how GitHub integration, queueing, DB, and MCP auth are configured.
- User asks for drift analysis between docs and implementation.

## Inputs
- Target repo root (default: current working directory).
- Optional environment name (`dev`, `staging`, `prod`).
- Optional comparison baseline (git ref or remote branch).

## Required outputs
1. `docs/env_map.md` style table (or inline equivalent) with:
   - variable name
   - owning component
   - required/optional
   - default value (if any)
   - fail-closed behavior when missing
   - source file locations
2. Contract drift report listing mismatches between docs and code.
3. Gate verdicts:
   - Artifact Contract Live
   - Execution Integrity Live
   - Runtime / Service Authority Live
   - Orchestration Live
   - Traceability Complete

## Workflow
1. Enumerate env usage from source with ripgrep (`os.environ`, `getenv`, settings objects).
2. Group by service boundary:
   - `control_plane/`
   - `worker/`
   - `mcp_server/`
   - shared runtime (`shared/`, compose/workflow files)
3. Mark each variable as `required` if startup/runtime hard-fails without it; otherwise `optional` and record fallback semantics.
4. Cross-check against docs (`README.md`, `docs/`, runbooks, CI workflows).
5. Produce a fail-closed assessment:
   - Missing required secret blocks startup/request path.
   - Unsafe default/fallback is a governance risk.
6. If asked to update artifacts, patch docs first, then code only when explicitly requested.

## GitHub-focused checks
When GitHub integration is in scope, verify and map:
- webhook secret enforcement
- app auth keys/installation wiring
- repo slug and API endpoint configuration
- PR operation runbook references

## Fail-closed rules
- Never mark a variable as safe if behavior silently degrades into data-loss mode.
- Explicitly flag `/tmp` persistence defaults, in-memory queue fallbacks, and unauthenticated tool paths.
- If evidence is incomplete, report `UNKNOWN` and block promotion.

## Minimal command set
- `rg -n "os\.environ|getenv|SESSION_LEDGER_DB_PATH|GITHUB|REDIS|DATABASE|MCP" <paths>`
- `python -m pytest -q` (when tests are requested)
- `python -m mypy .` (when type/contract validation is requested)

## Reporting template
Use this deterministic structure:
1. Current state (verified)
2. Risks / gaps
3. Proposed execution plan
4. Deliverables
5. Acceptance criteria
6. Next patch direction
