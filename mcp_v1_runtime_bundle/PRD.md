# PRD.md

## Product
MCP V1.0 — Single-Agent Orchestration Runtime

## Goal
Release a governed single-agent orchestration runtime that can generate, checkpoint, resume, and evaluate its own artifact bundle for MCP V1.0 using a LangGraph-based execution model.

## Scope
Included:
- generation manifest
- generation state schema
- TypeScript runtime module
- orchestration agent API
- embedded `Agent.md`, `SKILL.md`, and `tool-registry.json`
- A2A agent registry publication

Excluded:
- multi-agent execution
- external SaaS connectors
- deployment manifests
- production secrets management implementation

## Functional requirements
1. The runtime must use a graph/state model.
2. Every phase must be resumable from checkpoints.
3. The runtime must track token budgets and phase progress.
4. The runtime must expose an API for orchestration control and evaluation.
5. The release must publish an A2A registry entry.
6. The runtime must evaluate itself against this PRD.

## Non-functional requirements
- deterministic phase transitions
- fail-closed validation behavior
- machine-readable artifacts
- replay-safe workflow boundaries
- TypeScript-first implementation surface

## Acceptance criteria
| ID | Criterion | Pass condition |
|---|---|---|
| AC-01 | Manifest exists | `generation-manifest.json` created and internally consistent |
| AC-02 | State schema exists | `schemas/generation-state.schema.json` validates the runtime state model |
| AC-03 | Runtime module exists | `src/runtime/mcp-v1-runtime.ts` exports manifest, state contract, node contract, and graph factory |
| AC-04 | Embedded artifacts exist | module embeds `Agent.md`, `SKILL.md`, and tool registry contents |
| AC-05 | API exists | OpenAPI contract exists for orchestration agent |
| AC-06 | A2A registry exists | `Agents.md` and machine-readable registry entry are present |
| AC-07 | Checkpoint model exists | API and runtime model support checkpoint-aware execution |
| AC-08 | PRD evaluation exists | release can be evaluated against this file |

## Evaluation rubric
A release is **ready** when every acceptance criterion is satisfied and no critical validation finding remains open.
