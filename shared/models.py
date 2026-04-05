from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FixCIRequest(BaseModel):
    repo: str
    branch: str
    patch: str
    run_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    summary: Optional[str] = None
    trace_id: Optional[str] = None
    pr_url: Optional[str] = None


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
    channels: Dict[str, float | int]
    quality_flags: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("channels must not be empty")
        normalized: Dict[str, float | int] = {}
        for key, item in value.items():
            if not isinstance(item, (int, float)):
                raise ValueError(f"channel {key} must be numeric")
            normalized[key] = item
        return normalized


class EvidenceFeatures(BaseModel):
    brake_delta: Optional[float] = None
    turn_in_delta: Optional[float] = None
    apex_offset: Optional[float] = None
    throttle_delta: Optional[float] = None
    tire_temp_state: Optional[str] = None
    fuel_delta: Optional[float] = None
    confidence: Optional[float] = None


class EvidencePacket(BaseModel):
    evidence_packet_id: str
    session_id: str
    timestamp_logical_ns: int = Field(ge=0)
    timestamp_wall: Optional[datetime] = None
    severity: Literal["CRITICAL", "WARNING", "ADVISORY", "INFO", "NONE"]
    features: EvidenceFeatures


class Recommendation(BaseModel):
    recommendation_id: str
    evidence_packet_id: str
    priority: Literal["CRITICAL", "WARNING", "ADVISORY", "INFO", "NONE"]
    trigger: Optional[str] = None
    action: Optional[str] = None
    expected_effect: Optional[str] = None
    created_at_ns: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionEvidenceRequest(BaseModel):
    session_id: str
    principal_id: str = "system"
    policy_version: str = "rbac.v1"
    authz_scope: str = "session:write"
    run_id: Optional[str] = None
    trace_id: Optional[str] = None
    evidence_packets: List[EvidencePacket] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)


class SessionEvidenceResponse(BaseModel):
    status: Literal["ok"]
    stored: int
    receipts_created: int = 0
    latest_state_hash: Optional[str] = None


class SessionLedgerReplayResult(BaseModel):
    logical_clock: int
    valid: bool
    state_hash: str
    prev_hash: Optional[str] = None
    receipt_type: str
    status: str
    job_name: str


class SessionLedgerReplayResponse(BaseModel):
    session_id: str
    chain_ok: bool
    receipts: List[SessionLedgerReplayResult] = Field(default_factory=list)


class ReplayRequest(BaseModel):
    artifact_path: str
    sampling_hz: int = Field(default=60, ge=1, le=240)
    source: Literal["jsonl", "iracing_stream"] = "jsonl"
    max_frames: Optional[int] = Field(default=None, ge=1)
    strict: bool = True


class ReplayMetrics(BaseModel):
    frames_seen: int = 0
    frames_valid: int = 0
    frames_invalid: int = 0
    duration_ns: int = 0
    average_hz: float = 0.0
    max_tick_gap: int = 0
    duplicate_timestamps: int = 0
    missing_required_channels: List[str] = Field(default_factory=list)


class ReplayTask(BaseModel):
    task_id: str
    name: str
    status: Literal["pass", "fail", "warn"]
    detail: str


class ReplayResponse(BaseModel):
    replay_id: str
    status: Literal["accepted", "complete"]
    metrics: ReplayMetrics
    tasks: List[ReplayTask] = Field(default_factory=list)


class DirectStreamProbeRequest(BaseModel):
    duration_seconds: int = Field(default=10, ge=1, le=3600)
    sampling_hz: int = Field(default=60, ge=1, le=240)


class DirectStreamProbeResult(BaseModel):
    status: Literal["accepted", "complete"]
    metrics: ReplayMetrics
    tasks: List[ReplayTask]
    notes: List[str] = Field(default_factory=list)


class JSONLValidationResult(BaseModel):
    artifact_path: str
    lines_seen: int = 0
    valid_lines: int = 0
    invalid_lines: int = 0
    monotonic_timestamp_ns: bool = True
    monotonic_tick: bool = True
    missing_fields: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)


class AgentDecisionRequest(BaseModel):
    session_id: str
    run_id: str
    trace_id: str
    principal_id: str = "supervisor"
    policy_version: str = "rbac.v1"
    authz_scope: str = "agent:decision"
    evidence_packet_id: Optional[str] = None
    prompt: str
    provider: Literal["openai", "anthropic", "google", "openrouter"] = "openai"
    model: str = "gpt-4.1"
    metadata: Dict[str, Any] = Field(default_factory=dict)


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


class IngestSourceStatus(BaseModel):
    vendor: str
    native_extensions: List[str] = Field(default_factory=list)
    parser_module: Optional[str] = None
    available: bool = False
    notes: Optional[str] = None


class IngestNormalizeRequest(BaseModel):
    input_path: str
    output_dir: str
    vendor_hint: Optional[Literal["motec", "iracing", "aim", "vbox", "pi", "haltech", "aem", "csv_export"]] = None
    session_id: Optional[str] = None


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
    canonical_columns: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
