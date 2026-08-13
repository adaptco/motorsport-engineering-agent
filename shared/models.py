"""shared/models module."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FixCIRequest(BaseModel):
    repo: str
    branch: str
    patch: str
    run_id: str | None = None

    @field_validator("repo", "branch", "run_id")
    @classmethod
    def validate_safe_strings(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.startswith("-"):
            raise ValueError("String must not start with a hyphen to prevent option injection")
        if not re.match(r"^[a-zA-Z0-9._/-]+$", v):
            raise ValueError(f"String contains invalid characters: {v}")
        return v


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    summary: str | None = None
    trace_id: str | None = None
    pr_url: str | None = None


class TraceSpan(BaseModel):
    span_name: str
    status: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class TelemetryFrame(BaseModel):
    session_id: str
    driver_id: str
    track_id: str
    car_id: str
    timestamp_ns: int = Field(ge=0)
    tick: int = Field(ge=0)
    channels: dict[str, float | int]
    quality_flags: dict[str, Any] = Field(default_factory=dict)

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("channels must not be empty")
        normalized: dict[str, float | int] = {}
        for key, item in value.items():
            if not isinstance(item, (int, float)):
                raise ValueError(f"channel {key} must be numeric")
            normalized[key] = item
        return normalized


class EvidenceFeatures(BaseModel):
    brake_delta: float | None = None
    turn_in_delta: float | None = None
    apex_offset: float | None = None
    throttle_delta: float | None = None
    tire_temp_state: str | None = None
    fuel_delta: float | None = None
    confidence: float | None = None


class EvidencePacket(BaseModel):
    evidence_packet_id: str
    session_id: str
    timestamp_logical_ns: int = Field(ge=0)
    timestamp_wall: datetime | None = None
    severity: Literal["CRITICAL", "WARNING", "ADVISORY", "INFO", "NONE"]
    features: EvidenceFeatures


class Recommendation(BaseModel):
    recommendation_id: str
    evidence_packet_id: str
    priority: Literal["CRITICAL", "WARNING", "ADVISORY", "INFO", "NONE"]
    trigger: str | None = None
    action: str | None = None
    expected_effect: str | None = None
    created_at_ns: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionEvidenceRequest(BaseModel):
    session_id: str
    principal_id: str = "system"
    policy_version: str = "rbac.v1"
    authz_scope: str = "session:write"
    run_id: str | None = None
    trace_id: str | None = None
    evidence_packets: list[EvidencePacket] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)


class SessionEvidenceResponse(BaseModel):
    status: Literal["ok"]
    stored: int
    receipts_created: int = 0
    latest_state_hash: str | None = None


class SessionLedgerReplayResult(BaseModel):
    logical_clock: int
    valid: bool
    state_hash: str
    prev_hash: str | None = None
    receipt_type: str
    status: str
    job_name: str


class SessionLedgerReplayResponse(BaseModel):
    session_id: str
    chain_ok: bool
    receipts: list[SessionLedgerReplayResult] = Field(default_factory=list)


class ReplayRequest(BaseModel):
    artifact_path: str
    sampling_hz: int = Field(default=60, ge=1, le=240)
    source: Literal["jsonl", "iracing_stream"] = "jsonl"
    max_frames: int | None = Field(default=None, ge=1)
    strict: bool = True


class ReplayMetrics(BaseModel):
    frames_seen: int = 0
    frames_valid: int = 0
    frames_invalid: int = 0
    duration_ns: int = 0
    average_hz: float = 0.0
    max_tick_gap: int = 0
    duplicate_timestamps: int = 0
    missing_required_channels: list[str] = Field(default_factory=list)


class ReplayTask(BaseModel):
    task_id: str
    name: str
    status: Literal["pass", "fail", "warn"]
    detail: str


class ReplayResponse(BaseModel):
    replay_id: str
    status: Literal["accepted", "complete"]
    metrics: ReplayMetrics
    tasks: list[ReplayTask] = Field(default_factory=list)


class DirectStreamProbeRequest(BaseModel):
    duration_seconds: int = Field(default=10, ge=1, le=3600)
    sampling_hz: int = Field(default=60, ge=1, le=240)


class DirectStreamProbeResult(BaseModel):
    status: Literal["accepted", "complete"]
    metrics: ReplayMetrics
    tasks: list[ReplayTask]
    notes: list[str] = Field(default_factory=list)


class JSONLValidationResult(BaseModel):
    artifact_path: str
    lines_seen: int = 0
    valid_lines: int = 0
    invalid_lines: int = 0
    monotonic_timestamp_ns: bool = True
    monotonic_tick: bool = True
    missing_fields: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class AgentDecisionRequest(BaseModel):
    session_id: str
    run_id: str
    trace_id: str
    principal_id: str = "supervisor"
    policy_version: str = "rbac.v1"
    authz_scope: str = "agent:decision"
    evidence_packet_id: str | None = None
    prompt: str
    provider: Literal["openai", "anthropic", "google", "openrouter"] = "openai"
    model: str = "gpt-4.1"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentDecisionResponse(BaseModel):
    status: Literal["accepted", "scaffolded"]
    session_id: str
    run_id: str
    trace_id: str
    queued_job: str
    required_env: str
    supervisor_prompt_ref: str


class MCPToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPProviderStatus(BaseModel):
    provider: str
    env_var: str
    configured: bool


class A2AInvokeRequest(BaseModel):
    provider: Literal["openai", "anthropic", "google", "openrouter"]
    model: str
    prompt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class A2AInvokeResponse(BaseModel):
    status: Literal["scaffolded"]
    provider: str
    model: str
    required_env: str
    configured: bool
    message: str


RuntimeLocation = Literal["local", "worktree", "cloud"]
RuntimeTaskState = Literal["queued", "running", "blocked", "done"]
RuntimeEventType = Literal["agent_upsert", "task_upsert", "assignment_upsert", "heartbeat"]


class RuntimeAgentRecord(BaseModel):
    agent_id: str
    display_name: str
    runtime: RuntimeLocation
    host: str = "unknown"
    branch: str = "unknown"
    commit_hash: str = "unknown"
    dirty: bool = False
    note: str = ""
    last_seen_at: datetime


class RuntimeTaskRecord(BaseModel):
    task_id: str
    title: str
    state: RuntimeTaskState
    assigned_agent: str | None = None
    source: str = ""
    note: str = ""
    updated_by: str = "operator"
    updated_at: datetime


class RuntimeAgentUpsertPayload(BaseModel):
    agent_id: str
    display_name: str | None = None
    runtime: RuntimeLocation
    host: str = "unknown"
    branch: str = "unknown"
    commit_hash: str = "unknown"
    note: str = ""
    dirty: bool = False


class RuntimeTaskUpsertPayload(BaseModel):
    task_id: str
    title: str | None = None
    state: RuntimeTaskState
    source: str = ""
    note: str = ""
    updated_by: str = "operator"


class RuntimeAssignmentUpsertPayload(BaseModel):
    task_id: str
    agent_id: str | None = None
    updated_by: str = "operator"


class RuntimeHeartbeatPayload(BaseModel):
    agent_id: str
    at: datetime | None = None


class RuntimeStateAgentUpsertEvent(BaseModel):
    event_type: Literal["agent_upsert"]
    payload: RuntimeAgentUpsertPayload


class RuntimeStateTaskUpsertEvent(BaseModel):
    event_type: Literal["task_upsert"]
    payload: RuntimeTaskUpsertPayload


class RuntimeStateAssignmentUpsertEvent(BaseModel):
    event_type: Literal["assignment_upsert"]
    payload: RuntimeAssignmentUpsertPayload


class RuntimeStateHeartbeatEvent(BaseModel):
    event_type: Literal["heartbeat"]
    payload: RuntimeHeartbeatPayload


RuntimeStateEvent = (
    RuntimeStateAgentUpsertEvent
    | RuntimeStateTaskUpsertEvent
    | RuntimeStateAssignmentUpsertEvent
    | RuntimeStateHeartbeatEvent
)


class RuntimeStateMutationRequest(BaseModel):
    idempotency_key: str
    session_id: str
    event_type: RuntimeEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    client_ts: datetime | None = None


class RuntimeStateMutationResponse(BaseModel):
    status: Literal["accepted", "duplicate"]
    session_id: str
    applied_seq: int
    state_hash: str
    event_type: RuntimeEventType


class RuntimeStateSummary(BaseModel):
    agent_count: int
    runtime_counts: dict[str, int]
    task_counts: dict[str, int]


class RuntimeStateSnapshot(BaseModel):
    session_id: str
    generated_at: datetime
    last_seq: int
    last_state_hash: str
    summary: RuntimeStateSummary
    agents: dict[str, RuntimeAgentRecord] = Field(default_factory=dict)
    tasks: dict[str, RuntimeTaskRecord] = Field(default_factory=dict)


class RuntimeStateDeltaEvent(BaseModel):
    seq: int
    state_hash: str
    idempotency_key: str
    event_type: RuntimeEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    accepted_at: datetime


class RuntimeStateEventListResponse(BaseModel):
    session_id: str
    events: list[RuntimeStateDeltaEvent] = Field(default_factory=list)


class IngestSourceStatus(BaseModel):
    vendor: str
    native_extensions: list[str] = Field(default_factory=list)
    parser_module: str | None = None
    available: bool = False
    notes: str | None = None


class IngestNormalizeRequest(BaseModel):
    input_path: str
    output_dir: str
    vendor_hint: (
        Literal["motec", "iracing", "aim", "vbox", "pi", "haltech", "aem", "csv_export"] | None
    ) = None
    session_id: str | None = None


class IngestNormalizeResponse(BaseModel):
    status: Literal["complete"]
    vendor: str
    input_path: str
    output_dir: str
    normalized_csv: str
    channel_manifest_csv: str
    session_manifest_json: str
    row_count: int = 0
    column_count: int = 0
    canonical_columns: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AeroSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "photo", "cad", "telemetry", "public_reference", "measurement", "wind_tunnel", "solver_case"
    ]
    uri: str
    label: str | None = None
    sha256: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AeroVehicleIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    make: str
    model: str
    year: int | None = None
    trim: str | None = None
    chassis_code: str | None = None
    vehicle_class: str | None = None


class AeroSimulationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    vehicle_program_id: str
    vehicle_identity: AeroVehicleIdentity
    source_refs: list[AeroSourceRef] = Field(default_factory=list)
    simulation_objective: str
    baseline_geometry_strategy: Literal[
        "public_cad", "proxy_geometry", "imported_cad", "manual_sketch"
    ] = "proxy_geometry"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AeroSimulationBranchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_name: str
    change_mode: Literal["geometry", "setup", "solver", "boundary_condition"]
    change_summary: str
    requested_adjustments: dict[str, Any] = Field(default_factory=dict)
    expected_delta_cl: float | None = None
    expected_delta_cd: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AeroSimulationExecutionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runner_kind: Literal["sandbox", "wsl"]
    status: Literal["not_run", "queued", "running", "complete", "failed", "skipped"]
    environment: Literal["sandbox", "wsl2"]
    solver_status: Literal["scaffolded", "meshed", "solved", "failed", "archived"]
    distro_name: str | None = None
    distro_version: str | None = None
    openfoam_version: str | None = None
    kernel_signature: str | None = None
    command: list[str] = Field(default_factory=list)
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stdout_uri: str | None = None
    stderr_uri: str | None = None
    result_uri: str | None = None
    notes: list[str] = Field(default_factory=list)


class AeroSimulationSolveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solver_family: Literal["openfoam"] = "openfoam"
    execution_state: AeroSimulationExecutionState
    cl: float | None = None
    cd: float | None = None
    cm_pitch: float | None = None
    aero_balance_pct: float | None = None
    drag_area_m2: float | None = None
    downforce_n: float | None = None
    confidence: float = 0.0
    correlation_score: float | None = None
    residual_score: float | None = None
    artifacts: list[AeroSourceRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AeroSimulationStateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state_type: Literal["aero_simulation_state"] = "aero_simulation_state"
    state_version: int = 1
    simulation_run_id: str
    project_id: str
    vehicle_program_id: str
    loop_family: Literal["aero"] = "aero"
    loop_layer: Literal["simulation"] = "simulation"
    lifecycle_state: Literal[
        "draft", "baseline_built", "calibrating", "stable", "branching", "archived"
    ] = "draft"
    created_at: datetime
    updated_at: datetime
    state_hash: str
    prev_state_hash: str | None = None
    vehicle_snapshot: dict[str, Any]
    geometry_state: dict[str, Any]
    solver_state: dict[str, Any]
    metric_snapshot: dict[str, Any]
    provenance: list[AeroSourceRef] = Field(default_factory=list)
    branches: list[dict[str, Any]] = Field(default_factory=list)
    telemetry_links: list[AeroSourceRef] = Field(default_factory=list)
    calibration_state: dict[str, Any] = Field(default_factory=dict)
    resume_state: dict[str, Any] = Field(default_factory=dict)


class AeroSimulationStateSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_run_id: str
    project_id: str
    vehicle_program_id: str
    lifecycle_state: Literal[
        "draft", "baseline_built", "calibrating", "stable", "branching", "archived"
    ]
    state_hash: str
    updated_at: datetime
    state_path: str
