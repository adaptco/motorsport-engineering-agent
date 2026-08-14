# Control Plane Architecture Review

## Overview

The Control Plane is the central FastAPI application that orchestrates the
Motorsport Engineering Agent (MEA) system. It provides REST APIs for agent
decisions, session management, job execution, and GitHub integrations.

## Main Application Structure (control_plane/app.py)

The main FastAPI application is defined in `control_plane/app.py` with the
following components.

- **Routers Included**:
  - `github_router` (from `webhooks.py`) for GitHub webhook handling.
  - `session_router` for session evidence and ledger management.
  - `replay_router` for artifact replay functionality.
  - `verifier_router` for job execution and verification.
  - `agent_router` for AI agent decision processing.
- **Core Endpoints**:
  - `GET /healthz` for health status and kernel version.
  - `POST /repos/fix-ci` to queue CI fix jobs.
  - `GET /jobs/{job_id}` to retrieve job status.
  - `GET /jobs/{job_id}/trace` to retrieve execution traces.

## API Routes Analysis

### Agent Routes (routes/agent.py)

- `POST /agent/decision` processes agent decision requests.
  - Validates and queues decisions via `supervisor_service.queue_agent_decision`.
  - Appends forensic ledger receipts for audit trail.
  - Returns a decision response.

### Replay Routes (routes/replay.py)

- `POST /session/replay` replays session artifacts.
  - Uses `replay_service.replay_artifact` for processing.
  - Returns a replay response.

### Session Routes (routes/session.py)

- `POST /session/evidence` ingests session evidence packets.
  - Stores evidence batches and recommendations.
  - Returns an evidence response.
- `GET /session/{session_id}/replay-ledger` replays session ledger.
  - Verifies chain integrity.
  - Returns ledger replay results.

### Verifier Routes (routes/verifier.py)

- `POST /verifier/execute` executes verification jobs.
  - Uses `job_runner.execute_job` for processing.
  - Appends receipts and handles errors.
  - Returns execution results.

### GitHub Routes (webhooks.py)

- `POST /github/webhook` handles GitHub webhooks.
  - Verifies HMAC signatures for security.
  - Stores webhook events in the database.
  - Correlates workflow runs with jobs.

## Job Management System

### Queue System (queue.py)

- **Implementation**: Redis-backed queue with in-memory fallback.
- **Functions**:
  - `enqueue(job)` adds jobs to queue.
  - `dequeue(timeout)` retrieves jobs with timeout.
- **Purpose**: Asynchronous job processing pipeline.

### Repository Layer (repository.py)

- **Database Operations**:
  - Job lifecycle management (create, update, query).
  - Trace and span tracking.
  - Webhook event storage.
  - Session evidence persistence.
  - Workflow run correlation.
- **Key Functions**:
  - `create_job()` creates new jobs with UUIDs.
  - `update_job_phase()` updates job status and phases.
  - `get_job()` retrieves job details.
  - `list_trace()` gets execution traces.
  - `store_evidence_batch()` persists session data.
  - `replay_session_ledger()` verifies and replays ledgers.

## Webhook Integrations

### Webhook Handler (webhooks.py)

- **Security**: HMAC SHA256 signature verification.
- **Events**: Processes GitHub webhook payloads.
- **Storage**: Persists events in `webhook_events` table.
- **Correlation**: Links workflow runs to MEA jobs.

### GitHub App Integration (github_app.py)

- **Authentication**: JWT-based app authentication.
- **Token Management**: Creates installation access tokens.
- **API Access**: Enables authenticated GitHub API calls.

## Health Check Endpoints

- **Primary Health Check**: `GET /healthz`.
  - Returns `{"status": "ok", "kernel_version": "3.8", "package_version": "0.3.8"}`.
  - Used for liveness and readiness probes.
  - No dependencies required for basic health.

## Architecture Patterns

- **Asynchronous Processing**: Jobs are queued via Redis for worker processing.
- **Forensic Ledger**: Immutable audit trail for all operations.
- **Microservices Communication**: REST APIs with JSON payloads.
- **Security**: HMAC verification for webhooks and JWT for GitHub auth.
- **Data Persistence**: PostgreSQL for structured data and SQLite for ledgers.
- **Error Handling**: HTTP exceptions with detailed error messages.
- **Observability**: Traces, spans, and event logging.

## Dependencies

- FastAPI for the web framework.
- Redis for job queuing.
- PostgreSQL for data persistence.
- httpx for HTTP clients.
- PyJWT for GitHub authentication.
- Forensic ledger for audit trails.
