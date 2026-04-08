/**
 * MCP V1.0 Single-Agent Orchestration Runtime
 *
 * This module defines:
 * - generation manifest contract
 * - runtime state contract
 * - LangGraph node contract
 * - embedded Agent.md / SKILL.md / tool registry
 * - single-agent orchestration graph factory
 *
 * Notes:
 * - Nodes return Partial<GenerationState>.
 * - Compile the graph with a checkpointer in any resumable deployment.
 * - Invoke with a thread ID in config for checkpointed execution.
 */

import { Annotation, END, START, StateGraph } from "@langchain/langgraph";
import { createHash } from "node:crypto";

export const AGENT_MD = `# Agent.md

## Agent Identity
- **agent_id**: \`mcp-v1-orchestrator-single\`
- **name**: \`MCP V1 Orchestration Agent\`
- **mode**: single-agent governed runtime
- **release**: \`1.0.0\`
- **runtime**: TypeScript / Node.js / LangGraph

## Objective
Generate, validate, checkpoint, and evaluate a governed artifact bundle for a single-agent MCP V1 release against the product requirements in \`PRD.md\`.

## Responsibilities
1. Freeze generation scope from \`generation-manifest.json\`.
2. Generate schema, API, and code artifacts in deterministic phases.
3. Validate outputs before advancing phase state.
4. Persist checkpoints and compressed summaries between phases.
5. Evaluate the produced runtime against \`PRD.md\`.
6. Emit machine-readable evidence for release and replay.

## Capabilities
- manifest planning
- schema generation
- OpenAPI generation
- TypeScript runtime scaffolding
- checkpoint-aware execution
- PRD evaluation
- A2A registry publication
- MCP tool catalog exposure

## Non-negotiable invariants
1. The orchestrator is the only authority that advances run phase state.
2. Every node returns a partial state update only.
3. Every phase must checkpoint before downstream generation begins.
4. Mutating steps require an explicit permit in production mode.
5. Output evaluation must bind to \`PRD.md\` acceptance criteria.
6. Replay must resume from checkpoint state, never from raw chat history.

## Inputs
- \`generation-manifest.json\`
- \`schemas/generation-state.schema.json\`
- embedded skill + tool registry
- \`PRD.md\`

## Outputs
- phase summaries
- generated file set
- validation findings
- PRD evaluation report
- agent registry entry for A2A

## Failure policy
- fail closed on invalid schema, invalid OpenAPI, unresolved references, or exhausted budget
- generate repair work items instead of silently mutating prior validated outputs

## Observability
The agent emits:
- run events
- checkpoint metadata
- token usage by phase
- validation findings
- PRD evaluation status

## Release gate
The release is only considered ready when:
- all planned files exist
- validation passes
- PRD acceptance criteria are satisfied
- agent registry entry is published
- API contract and state schema are internally consistent
`;
export const SKILL_MD = `# SKILL.md

## Skill Name
\`mcp-v1-single-agent-release\`

## Purpose
This skill drives a checkpointed, resumable generation workflow for a single-agent MCP V1 runtime.

## Operating model
Use a graph-based runtime with explicit phase transitions:
1. \`freeze_plan\`
2. \`generate_schemas\`
3. \`generate_openapi\`
4. \`generate_runtime_module\`
5. \`generate_registry_and_docs\`
6. \`evaluate_release\`

Each phase:
- consumes bounded context
- writes machine-readable outputs
- runs local validation
- writes a checkpoint
- emits a compact summary for downstream context

## Required files
- \`generation-manifest.json\`
- \`schemas/generation-state.schema.json\`
- \`src/runtime/mcp-v1-runtime.ts\`
- \`openapi/orchestration-agent.openapi.yaml\`
- \`Agent.md\`
- \`Agents.md\`
- \`tool-registry.json\`
- \`PRD.md\`

## Hot / warm / cold context
- **hot**: current phase targets, local dependencies, validator errors
- **warm**: manifest, reference map, compressed phase summaries
- **cold**: completed file bodies, prior receipts, archived diagnostics

## Checkpoint rules
Checkpoint after every successful phase. A checkpoint record must include:
- \`checkpoint_id\`
- \`thread_id\`
- \`phase\`
- \`completed_files\`
- \`manifest_digest\`
- \`context_summary\`
- \`token_usage\`
- \`next_phase\`

## Quality gates
### Schemas
- valid JSON
- unique \`$id\`
- stable refs

### OpenAPI
- valid OpenAPI 3.1
- unique \`operationId\`
- response models align to generation state and manifest contracts

### TypeScript
- parseable module
- node contract and state contract align
- no placeholder production TODOs

### Release evaluation
- planned file count == generated file count
- PRD acceptance criteria marked pass / fail with evidence

## Tool usage policy
Only use tools declared in \`tool-registry.json\`.
In production mode:
- side-effectful tools require permits
- non-deterministic operations must be wrapped in tasks
- replay must reuse checkpointed outputs instead of reissuing side effects

## A2A publication
Publish the final orchestration agent entry to:
- \`Agents.md\`
- \`registry/agents.registry.json\`
`;

export const TOOL_REGISTRY = {
  "$schema": "https://example.org/schemas/tool-registry.schema.json",
  "registry_id": "mcp-v1-single-agent-tool-registry",
  "version": "1.0.0",
  "tools": [
    {
      "name": "manifest.freeze",
      "description": "Freeze the generation manifest and derive phase/ref maps.",
      "side_effect_class": "none",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "manifestPath"
        ],
        "properties": {
          "manifestPath": {
            "type": "string"
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "manifestDigest",
          "phasePlan"
        ],
        "properties": {
          "manifestDigest": {
            "type": "string"
          },
          "phasePlan": {
            "type": "object"
          }
        }
      }
    },
    {
      "name": "schema.generate",
      "description": "Generate a schema family from the frozen manifest.",
      "side_effect_class": "file_write",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "family",
          "targets"
        ],
        "properties": {
          "family": {
            "type": "string"
          },
          "targets": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "writtenFiles"
        ],
        "properties": {
          "writtenFiles": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    {
      "name": "openapi.generate",
      "description": "Generate an OpenAPI contract and components for the orchestration agent.",
      "side_effect_class": "file_write",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "resourceGroup"
        ],
        "properties": {
          "resourceGroup": {
            "type": "string"
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "writtenFiles"
        ],
        "properties": {
          "writtenFiles": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    {
      "name": "typescript.generate",
      "description": "Generate the governed TypeScript runtime module.",
      "side_effect_class": "file_write",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "modulePath"
        ],
        "properties": {
          "modulePath": {
            "type": "string"
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "modulePath"
        ],
        "properties": {
          "modulePath": {
            "type": "string"
          }
        }
      }
    },
    {
      "name": "validate.bundle",
      "description": "Run bundle validation across JSON, YAML, and TypeScript surfaces.",
      "side_effect_class": "none",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "paths"
        ],
        "properties": {
          "paths": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "passed",
          "findings"
        ],
        "properties": {
          "passed": {
            "type": "boolean"
          },
          "findings": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    {
      "name": "checkpoint.write",
      "description": "Persist a phase checkpoint summary.",
      "side_effect_class": "checkpoint_write",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "phase",
          "completedFiles"
        ],
        "properties": {
          "phase": {
            "type": "string"
          },
          "completedFiles": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "checkpointId"
        ],
        "properties": {
          "checkpointId": {
            "type": "string"
          }
        }
      }
    },
    {
      "name": "prd.evaluate",
      "description": "Evaluate generated outputs against PRD acceptance criteria.",
      "side_effect_class": "none",
      "idempotent": true,
      "args_schema": {
        "type": "object",
        "required": [
          "prdPath",
          "manifestPath"
        ],
        "properties": {
          "prdPath": {
            "type": "string"
          },
          "manifestPath": {
            "type": "string"
          }
        }
      },
      "result_schema": {
        "type": "object",
        "required": [
          "status",
          "criteria"
        ],
        "properties": {
          "status": {
            "type": "string"
          },
          "criteria": {
            "type": "array",
            "items": {
              "type": "object"
            }
          }
        }
      }
    }
  ]
} as const;

export const GENERATION_MANIFEST = {
  "$schema": "./schemas/generation-manifest.schema.json",
  "manifest_id": "mcp-v1-single-agent-generation-manifest",
  "version": "1.0.0",
  "objective": "Generate a complete governed single-agent MCP V1 release bundle.",
  "release": {
    "name": "mcp-v1-single-agent",
    "version": "1.0.0",
    "mode": "single-agent",
    "runtime": "typescript-langgraph"
  },
  "token_budget": {
    "total": 180000,
    "repair_reserve": 30000,
    "per_phase_limit": 35000,
    "per_node_limit": 12000
  },
  "phases": [
    {
      "phase_id": "freeze_plan",
      "description": "Freeze manifest and derive reference map.",
      "outputs": [
        "generation-manifest.json"
      ],
      "depends_on": []
    },
    {
      "phase_id": "generate_schemas",
      "description": "Generate state and supporting schemas.",
      "outputs": [
        "schemas/generation-state.schema.json"
      ],
      "depends_on": [
        "freeze_plan"
      ]
    },
    {
      "phase_id": "generate_runtime_module",
      "description": "Generate the governed TypeScript runtime module.",
      "outputs": [
        "src/runtime/mcp-v1-runtime.ts"
      ],
      "depends_on": [
        "generate_schemas"
      ]
    },
    {
      "phase_id": "generate_docs_and_registry",
      "description": "Generate embedded markdown and A2A registry assets.",
      "outputs": [
        "Agent.md",
        "SKILL.md",
        "tool-registry.json",
        "Agents.md",
        "registry/agents.registry.json"
      ],
      "depends_on": [
        "generate_runtime_module"
      ]
    },
    {
      "phase_id": "generate_api",
      "description": "Generate orchestration agent API contract.",
      "outputs": [
        "openapi/orchestration-agent.openapi.yaml"
      ],
      "depends_on": [
        "generate_runtime_module",
        "generate_docs_and_registry"
      ]
    },
    {
      "phase_id": "evaluate_release",
      "description": "Evaluate release against PRD acceptance criteria.",
      "outputs": [
        "PRD.md",
        "docs/prd-evaluation.template.json"
      ],
      "depends_on": [
        "generate_api"
      ]
    }
  ],
  "planned_files": [
    {
      "path": "generation-manifest.json",
      "kind": "json",
      "owner_phase": "freeze_plan"
    },
    {
      "path": "schemas/generation-state.schema.json",
      "kind": "json",
      "owner_phase": "generate_schemas"
    },
    {
      "path": "src/runtime/mcp-v1-runtime.ts",
      "kind": "typescript",
      "owner_phase": "generate_runtime_module"
    },
    {
      "path": "Agent.md",
      "kind": "markdown",
      "owner_phase": "generate_docs_and_registry"
    },
    {
      "path": "SKILL.md",
      "kind": "markdown",
      "owner_phase": "generate_docs_and_registry"
    },
    {
      "path": "tool-registry.json",
      "kind": "json",
      "owner_phase": "generate_docs_and_registry"
    },
    {
      "path": "Agents.md",
      "kind": "markdown",
      "owner_phase": "generate_docs_and_registry"
    },
    {
      "path": "registry/agents.registry.json",
      "kind": "json",
      "owner_phase": "generate_docs_and_registry"
    },
    {
      "path": "PRD.md",
      "kind": "markdown",
      "owner_phase": "evaluate_release"
    },
    {
      "path": "docs/prd-evaluation.template.json",
      "kind": "json",
      "owner_phase": "evaluate_release"
    },
    {
      "path": "openapi/orchestration-agent.openapi.yaml",
      "kind": "yaml",
      "owner_phase": "generate_api"
    }
  ],
  "embedded_artifacts": [
    {
      "name": "Agent.md",
      "target_module_export": "AGENT_MD"
    },
    {
      "name": "SKILL.md",
      "target_module_export": "SKILL_MD"
    },
    {
      "name": "tool-registry.json",
      "target_module_export": "TOOL_REGISTRY"
    }
  ],
  "evaluation_target": {
    "prd_path": "PRD.md",
    "mode": "single-agent"
  }
} as const;

export type PhaseId =
  | "freeze_plan"
  | "generate_schemas"
  | "generate_runtime_module"
  | "generate_docs_and_registry"
  | "generate_api"
  | "evaluate_release";

export type RunStatus =
  | "idle"
  | "running"
  | "paused"
  | "blocked"
  | "completed"
  | "failed";

export interface CheckpointRecord {
  checkpoint_id: string;
  phase: string;
  completed_files: string[];
  manifest_digest: string;
  context_summary: string;
  token_usage: number;
  next_phase: string;
}

export interface GenerationStateShape {
  run_id: string;
  thread_id: string;
  objective: string;
  release_version: string;
  active_phase: PhaseId;
  active_task: string;
  status: RunStatus;
  completed_tasks: string[];
  planned_files: string[];
  generated_files: Record<string, string>;
  validated_files: string[];
  failed_files: string[];
  current_manifest?: Record<string, unknown>;
  schema_refs?: Record<string, string>;
  openapi_refs?: Record<string, string>;
  token_budget_total: number;
  token_budget_remaining: number;
  token_budget_phase_limit: number;
  token_usage_by_phase: Record<string, number>;
  context_summary: string;
  quality_findings: string[];
  last_checkpoint_id?: string | null;
  replay_from_phase?: string | null;
  checkpoints: CheckpointRecord[];
}

export interface PhaseExecutionResult {
  writtenFiles: string[];
  validatedFiles: string[];
  findings: string[];
  tokenUsage: number;
  summary: string;
}

export interface PRDEvaluationCriterion {
  id: string;
  status: "pass" | "fail" | "pending";
  evidence: string[];
}

export interface PRDEvaluationResult {
  status: "ready" | "not_ready";
  criteria: PRDEvaluationCriterion[];
  summary: string;
}

export interface GenerationExecutor {
  freezePlan(state: GenerationStateShape): Promise<PhaseExecutionResult>;
  generateSchemas(state: GenerationStateShape): Promise<PhaseExecutionResult>;
  generateRuntimeModule(state: GenerationStateShape): Promise<PhaseExecutionResult>;
  generateDocsAndRegistry(state: GenerationStateShape): Promise<PhaseExecutionResult>;
  generateApi(state: GenerationStateShape): Promise<PhaseExecutionResult>;
  evaluateRelease(state: GenerationStateShape): Promise<PRDEvaluationResult>;
}

export interface RuntimeGraphOptions {
  executor: GenerationExecutor;
  checkpointer?: unknown;
}

export interface NodeContract {
  nodeId: PhaseId;
  description: string;
  consumes: string[];
  produces: string[];
  requiresCheckpointOnSuccess: boolean;
  budgetPolicy: {
    phaseLimitKey: "token_budget_phase_limit";
    remainingBudgetKey: "token_budget_remaining";
  };
}

export const NODE_CONTRACTS: Record<PhaseId, NodeContract> = {
  freeze_plan: {
    nodeId: "freeze_plan",
    description: "Freeze manifest and derive phase-local references.",
    consumes: ["generation-manifest.json", "PRD.md"],
    produces: ["manifest digest", "ref map", "checkpoint"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
  generate_schemas: {
    nodeId: "generate_schemas",
    description: "Generate and validate the runtime state schema.",
    consumes: ["generation-manifest.json"],
    produces: ["schemas/generation-state.schema.json", "checkpoint"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
  generate_runtime_module: {
    nodeId: "generate_runtime_module",
    description: "Generate the governed TypeScript runtime module.",
    consumes: ["schemas/generation-state.schema.json", "Agent.md", "SKILL.md", "tool-registry.json"],
    produces: ["src/runtime/mcp-v1-runtime.ts", "checkpoint"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
  generate_docs_and_registry: {
    nodeId: "generate_docs_and_registry",
    description: "Generate embedded markdown artifacts and A2A registry outputs.",
    consumes: ["src/runtime/mcp-v1-runtime.ts"],
    produces: ["Agent.md", "SKILL.md", "tool-registry.json", "Agents.md", "registry/agents.registry.json", "checkpoint"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
  generate_api: {
    nodeId: "generate_api",
    description: "Generate the orchestration agent OpenAPI contract.",
    consumes: ["src/runtime/mcp-v1-runtime.ts", "Agents.md"],
    produces: ["openapi/orchestration-agent.openapi.yaml", "checkpoint"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
  evaluate_release: {
    nodeId: "evaluate_release",
    description: "Evaluate the generated bundle against PRD acceptance criteria.",
    consumes: ["PRD.md", "generation-manifest.json", "openapi/orchestration-agent.openapi.yaml"],
    produces: ["evaluation result"],
    requiresCheckpointOnSuccess: true,
    budgetPolicy: {
      phaseLimitKey: "token_budget_phase_limit",
      remainingBudgetKey: "token_budget_remaining",
    },
  },
};

export const GenerationState = Annotation.Root({
  run_id: Annotation<string>,
  thread_id: Annotation<string>,
  objective: Annotation<string>,
  release_version: Annotation<string>,
  active_phase: Annotation<PhaseId>,
  active_task: Annotation<string>,
  status: Annotation<RunStatus>,
  completed_tasks: Annotation<string[]>({
    reducer: (left, right) => [...(left ?? []), ...(right ?? [])],
    default: () => [],
  }),
  planned_files: Annotation<string[]>({
    reducer: (_, right) => right ?? [],
    default: () => [],
  }),
  generated_files: Annotation<Record<string, string>>({
    reducer: (left, right) => ({ ...(left ?? {}), ...(right ?? {}) }),
    default: () => ({}),
  }),
  validated_files: Annotation<string[]>({
    reducer: (left, right) => [...(left ?? []), ...(right ?? [])],
    default: () => [],
  }),
  failed_files: Annotation<string[]>({
    reducer: (left, right) => [...(left ?? []), ...(right ?? [])],
    default: () => [],
  }),
  current_manifest: Annotation<Record<string, unknown> | undefined>({
    reducer: (_, right) => right,
    default: () => undefined,
  }),
  schema_refs: Annotation<Record<string, string> | undefined>({
    reducer: (left, right) => ({ ...(left ?? {}), ...(right ?? {}) }),
    default: () => undefined,
  }),
  openapi_refs: Annotation<Record<string, string> | undefined>({
    reducer: (left, right) => ({ ...(left ?? {}), ...(right ?? {}) }),
    default: () => undefined,
  }),
  token_budget_total: Annotation<number>,
  token_budget_remaining: Annotation<number>,
  token_budget_phase_limit: Annotation<number>,
  token_usage_by_phase: Annotation<Record<string, number>>({
    reducer: (left, right) => ({ ...(left ?? {}), ...(right ?? {}) }),
    default: () => ({}),
  }),
  context_summary: Annotation<string>({
    reducer: (_, right) => right ?? "",
    default: () => "",
  }),
  quality_findings: Annotation<string[]>({
    reducer: (left, right) => [...(left ?? []), ...(right ?? [])],
    default: () => [],
  }),
  last_checkpoint_id: Annotation<string | null>({
    reducer: (_, right) => right ?? null,
    default: () => null,
  }),
  replay_from_phase: Annotation<string | null>({
    reducer: (_, right) => right ?? null,
    default: () => null,
  }),
  checkpoints: Annotation<CheckpointRecord[]>({
    reducer: (left, right) => [...(left ?? []), ...(right ?? [])],
    default: () => [],
  }),
});

export type GenerationState = typeof GenerationState.State;

function sha256Hex(input: string): string {
  return `sha256:${createHash("sha256").update(input, "utf8").digest("hex")}`;
}

function makeCheckpoint(
  phase: PhaseId,
  completedFiles: string[],
  manifestDigest: string,
  contextSummary: string,
  tokenUsage: number,
  nextPhase: string,
): CheckpointRecord {
  return {
    checkpoint_id: `ckpt_${phase}_${Date.now()}`,
    phase,
    completed_files: completedFiles,
    manifest_digest: manifestDigest,
    context_summary: contextSummary,
    token_usage: tokenUsage,
    next_phase: nextPhase,
  };
}

function applyPhaseResult(
  state: GenerationState,
  phase: PhaseId,
  result: PhaseExecutionResult,
  nextPhase: PhaseId,
): Partial<GenerationState> {
  const manifestDigest = sha256Hex(JSON.stringify(GENERATION_MANIFEST));
  const checkpoint = makeCheckpoint(
    phase,
    result.writtenFiles,
    manifestDigest,
    result.summary,
    result.tokenUsage,
    nextPhase,
  );

  return {
    active_phase: nextPhase,
    active_task: nextPhase,
    status: "running",
    completed_tasks: [phase],
    generated_files: Object.fromEntries(result.writtenFiles.map((path) => [path, "generated"])),
    validated_files: result.validatedFiles,
    token_budget_remaining: Math.max(0, state.token_budget_remaining - result.tokenUsage),
    token_usage_by_phase: { [phase]: result.tokenUsage },
    context_summary: result.summary,
    quality_findings: result.findings,
    last_checkpoint_id: checkpoint.checkpoint_id,
    checkpoints: [checkpoint],
  };
}

export function buildInitialState(runId: string, threadId: string): GenerationStateShape {
  return {
    run_id: runId,
    thread_id: threadId,
    objective: GENERATION_MANIFEST.objective,
    release_version: GENERATION_MANIFEST.release.version,
    active_phase: "freeze_plan",
    active_task: "freeze_plan",
    status: "idle",
    completed_tasks: [],
    planned_files: GENERATION_MANIFEST.planned_files.map((f) => f.path),
    generated_files: {},
    validated_files: [],
    failed_files: [],
    current_manifest: GENERATION_MANIFEST as unknown as Record<string, unknown>,
    schema_refs: {
      generation_state: "schemas/generation-state.schema.json",
    },
    openapi_refs: {
      orchestration_agent: "openapi/orchestration-agent.openapi.yaml",
    },
    token_budget_total: GENERATION_MANIFEST.token_budget.total,
    token_budget_remaining: GENERATION_MANIFEST.token_budget.total,
    token_budget_phase_limit: GENERATION_MANIFEST.token_budget.per_phase_limit,
    token_usage_by_phase: {},
    context_summary: "",
    quality_findings: [],
    last_checkpoint_id: null,
    replay_from_phase: null,
    checkpoints: [],
  };
}

export function createSingleAgentRuntimeGraph(options: RuntimeGraphOptions) {
  const { executor, checkpointer } = options;

  const graph = new StateGraph(GenerationState)
    .addNode("freeze_plan", async (state: GenerationState) => {
      const result = await executor.freezePlan(state);
      return applyPhaseResult(state, "freeze_plan", result, "generate_schemas");
    })
    .addNode("generate_schemas", async (state: GenerationState) => {
      const result = await executor.generateSchemas(state);
      return applyPhaseResult(state, "generate_schemas", result, "generate_runtime_module");
    })
    .addNode("generate_runtime_module", async (state: GenerationState) => {
      const result = await executor.generateRuntimeModule(state);
      return applyPhaseResult(state, "generate_runtime_module", result, "generate_docs_and_registry");
    })
    .addNode("generate_docs_and_registry", async (state: GenerationState) => {
      const result = await executor.generateDocsAndRegistry(state);
      return applyPhaseResult(state, "generate_docs_and_registry", result, "generate_api");
    })
    .addNode("generate_api", async (state: GenerationState) => {
      const result = await executor.generateApi(state);
      return applyPhaseResult(state, "generate_api", result, "evaluate_release");
    })
    .addNode("evaluate_release", async (state: GenerationState) => {
      const evaluation = await executor.evaluateRelease(state);
      const passed = evaluation.status === "ready";
      return {
        active_phase: "evaluate_release",
        active_task: "complete",
        status: passed ? "completed" : "failed",
        context_summary: evaluation.summary,
        quality_findings: evaluation.criteria
          .filter((c) => c.status !== "pass")
          .map((c) => `${c.id}: ${c.status}`),
      } satisfies Partial<GenerationState>;
    })
    .addEdge(START, "freeze_plan")
    .addEdge("freeze_plan", "generate_schemas")
    .addEdge("generate_schemas", "generate_runtime_module")
    .addEdge("generate_runtime_module", "generate_docs_and_registry")
    .addEdge("generate_docs_and_registry", "generate_api")
    .addEdge("generate_api", "evaluate_release")
    .addEdge("evaluate_release", END);

  return graph.compile(checkpointer ? { checkpointer } : undefined);
}

export const RELEASE_RUNTIME_PROFILE = {
  release: "mcp-v1-single-agent",
  version: "1.0.0",
  protocol: "MCP V1",
  agentMode: "single-agent",
  entrypoint: "src/runtime/mcp-v1-runtime.ts",
  apiContract: "openapi/orchestration-agent.openapi.yaml",
  registry: "registry/agents.registry.json",
} as const;
