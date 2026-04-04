<!-- markdownlint-disable MD013 MD024 MD025 MD036 MD040 -->

# MEA Codebase Review Report

## Executive Summary

The Motorsport Engineering Agent (MEA) is a containerized Python-based system that integrates AI decision-making with telemetry ingestion and GitHub automation. It combines a FastAPI control plane, an MCP server for multi-provider LLM tool orchestration, and a worker backend for job execution and audit logging. The system is designed to process iRacing simulator telemetry, make engineering recommendations, and automate CI and repository workflows with secure, auditable operations.

## Architecture Overview

MEA follows a multi-service architecture with clear separation of concerns:

- **Control Plane**: FastAPI application exposing REST APIs for agent decisions, session evidence ingestion, job verification, replay, and GitHub webhook handling.
- **MCP Server**: Model Context Protocol server supporting LLM provider integration, tool execution, and agent-to-agent invocations.
- **Worker**: Background job processor handling Redis-queued jobs, GitHub operations, and forensic ledger writing.
- **Data Layer**: PostgreSQL for structured persistence, Redis for queueing, and SQLite-based forensic ledger for audit trails.

### High-Level Data Flow

1. **Telemetry ingestion** from the iRacing simulator enters through the session evidence API.
2. **Evidence validation and processing** convert raw telemetry into structured packets and recommendations.
3. **AI analysis** is performed by the supervisor/policy engine using MCP server tools and LLM providers.
4. **Jobs are queued** in Redis and executed by the worker backend.
5. **GitHub integration** manages PR creation, reviews, and developer workflow automation.

## Component Descriptions

### Control Plane

- `control_plane/app.py`: Main FastAPI application that wires routers and core middleware.
- `control_plane/routes/agent.py`: Agent decision API for queuing, validating, and processing AI decision requests.
- `control_plane/routes/session.py`: Session evidence ingestion, session ledger replay, and session management.
- `control_plane/routes/replay.py`: Replay API for artifact replay functionality.
- `control_plane/routes/verifier.py`: Job execution and verification endpoints.
- `control_plane/webhooks.py`: GitHub webhook handler with HMAC verification and event correlation.
- `control_plane/queue.py`: Redis-backed queue implementation with in-memory fallback.
- `control_plane/repository.py`: Database access layer for jobs, evidence, traces, and session persistence.

### MCP Server

- `mcp_server/app.py`: MCP server application handling provider orchestration and tool calls.
- `mcp_tools/__init__.py`: Entry point used by the Docker image.
- `mea_ci_guardrail.py`: CI quality and patch safety tool used by the MCP server.

### Worker Backend

- `worker/backend_worker.py`: Main worker loop and job processing orchestration.
- `worker/github_app_client.py`: GitHub App client for installation token generation and API calls.
- `worker/repository.py`: Worker-specific repository helpers for job lifecycle management.

### Ingestion and Telemetry

- `ingest/iracing_stream.py`: iRacing telemetry ingestion and stream processing.
- `shared/models.py`: Telemetry and replay data models used across the system.
- `shared/jsonl_validator.py`: JSONL validation utilities for telemetry data ingestion.

### Shared Infrastructure

- `shared/db.py`: Database connection and session management.
- `shared/forensic_ledger.py`: Immutable audit trail mechanisms.
- `shared/models.py`: Shared domain models and schemas.

## Key Workflows

### Telemetry Ingestion Workflow

- Telemetry data is submitted via `POST /session/evidence`.
- JSONL frames are validated and stored in PostgreSQL.
- Evidence packets are enriched and persisted in `evidence_packets`.
- Recommendations are generated and stored in `recommendations_runtime`.

### Decision Workflow

- Decision requests enter via `POST /agent/decision`.
- Supervisor service validates and queues decisions.
- Jobs are enqueued into Redis and processed asynchronously.
- Worker execution results are logged in the forensic ledger and persisted.

### GitHub Automation Workflow

- GitHub webhooks are received at `POST /github/webhook`.
- HMAC verification protects webhook payload authenticity.
- Worker backend uses GitHub App authentication to create PRs, reviews, and manage repos.
- CI guardrails inspect patches before application.

### Job Execution Workflow

- Jobs created with UUIDs are stored in `jobs`.
- Worker dequeues jobs from Redis and advances job phases.
- Execution traces are stored for audit and replay.
- Completed jobs update status and evidence in the database.

## Technology Assessment

### Core Stack

- **Python**: Primary language, required version >= 3.11, verified with 3.13.7.
- **FastAPI**: Main web framework for the control plane.
- **Uvicorn**: ASGI server used in the Docker runtime.
- **PostgreSQL**: Structured storage for jobs, evidence, sessions, and webhooks.
- **Redis**: Queueing and caching.
- **SQLite / Forensic Ledger**: Immutable audit trail storage.
- **Docker**: Containerization of control plane, MCP server, and worker.

### Dependencies and Tools

- **Pydantic**: Data validation and serialization.
- **psycopg[binary]**: PostgreSQL driver.
- **redis**: Redis client.
- **PyJWT / cryptography**: Authentication and secure operations.
- **httpx**: HTTP client.
- **pytest / pytest-cov**: Testing and coverage.
- **Typer**: CLI tooling.

## Security Considerations

- Secure webhook handling with HMAC SHA256 signature verification.
- GitHub App authentication via JWT and installation tokens.
- Input validation through Pydantic models to reduce injection risk.
- Forensic ledger provides cryptographically auditable receipts.
- MCP server and tool access require authentication.
- Sensitive data handling should remain isolated from patch generation logic.

## Recommendations

- Add a dedicated architecture diagram file to complement the review report.
- Expand the MCP server documentation with provider configuration and authentication flows.
- Add example telemetry ingestion payloads and session evidence API usage docs.
- Document worker retry and backoff policies for failed jobs.
- Add explicit security review checklist for GitHub App operations.
- Include monitoring guidance for Redis queue health and PostgreSQL performance.

## Conclusion

The MEA codebase is a well-structured system that combines telemetry ingestion, AI-driven decision workflows, and GitHub automation. The architecture supports secure, auditable operations and is extensible to additional LLM providers and telemetry sources. Incremental documentation improvements and more explicit workflow diagrams will strengthen long-term maintainability.
