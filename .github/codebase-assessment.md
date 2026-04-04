# Motorsport Engineering Agent - Codebase Assessment

**Assessment Date:** 2026-04-04  
**Repository:** motorsport-engineering-agent  
**Current Version:** Kernel V3.4, Package 0.3.4  
**Language:** Python 3.11+  

---

## Table of Contents

1. [Repository Structure & Architecture](#repository-structure--architecture)
2. [Key Components & Modules](#key-components--modules)
3. [Code Quality Assessment](#code-quality-assessment)
4. [DevOps & Deployment](#devops--deployment)
5. [Dependencies & External Integrations](#dependencies--external-integrations)
6. [Current State Observations](#current-state-observations)
7. [Key Recommendations](#key-recommendations)
8. [Review Focus Priority](#review-focus-priority)

---

## Repository Structure & Architecture

### Directory Organization

The repository follows a **component-based monorepo** structure with clear separation of concerns:

- **`control_plane/`** - FastAPI orchestration hub (port 8000)
  - `app.py` - Main application with routers
  - `routes/` - API endpoints (agent, replay, session, verifier)
  - `services/` - Business logic (supervisor, replay, job execution)
  - `webhooks.py` - GitHub webhook ingestion
  - `queue.py` - Redis/memory-based job queue
  - `repository.py` - Data persistence (PostgreSQL)

- **`mcp_server/`** - Model Context Protocol LLM gateway
  - Exposes OpenAI, Anthropic, Google, OpenRouter providers
  - Bearer token authentication support

- **`worker/`** - Background job processor
  - `backend_worker.py` - Main loop for job consumption and execution
  - `github_app_client.py` - GitHub App authentication

- **`mea/`** - Core reasoning engine
  - `policy_engine.py` - Priority queue with logical clock and cooldown enforcement
  - `time_domains.py` - Time abstraction (DATA vs WALL)

- **`shared/`** - Cross-service utilities
  - `models.py` - Pydantic data models
  - `forensic_ledger.py` - Append-only audit log (SQLite)
  - `jsonl_validator.py` - JSONL telemetry validation
  - `db.py` - PostgreSQL connection

- **`ingest/`** - Data adapters
  - `iracing_stream.py` - iRacing telemetry (Windows-only)

- **`tests/`** - Test suite (unit + integration)
- **`docs/`** - Architecture docs (supervisor-loop, versioning-spec, monorepo-review)
- **`db/migrations/`** - PostgreSQL schema (3 migrations)
- **`configs/`** - Model weights configuration

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Python | 3.11+ |
| Web Framework | FastAPI | 0.115+ |
| ASGI Server | Uvicorn | 0.30+ |
| Process Manager | Gunicorn | 21.2+ |
| Primary DB | PostgreSQL | - |
| Cache/Queue | Redis | 5.0+ |
| Audit Log | SQLite | - |
| Validation | Pydantic | 2.8+ |
| Testing | pytest | 8.3+ |
| Linting | ruff | (CI) |
| Type Checking | mypy | (CI) |

---

## Key Components & Modules

### Control Plane (`control_plane/`)
- Main orchestration API for job lifecycle and CI automation
- Endpoints: `/repos/fix-ci`, `/jobs/{id}`, `/agent/decision`, `/healthz`
- Includes GitHub webhook ingestion with HMAC-SHA256 verification
- Routes to services (supervisor, replay, job runner, session management)

### Policy Engine (`mea/reasoning/policy_engine.py`)
- Deterministic recommendation queue with priority ranking
- Priorities: CRITICAL > WARNING > ADVISORY > INFO > NONE
- Features: TTL enforcement, cooldown throttling, logical clock semantics
- Thread-safe with RLock protection
- Configuration in `configs/model_weights.yaml`

### Forensic Ledger (`shared/forensic_ledger.py`)
- Append-only SQLite audit log for complete traceability
- Cryptographic state hashing (sha256-prefixed canonical JSON)
- Uniqueness constraints on (session_id, logical_clock) and state_hash
- Full command vector recording with metadata

### JSONL Validator (`shared/jsonl_validator.py`)
- Strict telemetry stream validation
- Checks: required fields, numeric channels, monotonic timestamps, strict ticks
- Pydantic schema validation per line
- Duplicate timestamp and tick gap detection

### Job Runner (`control_plane/services/job_runner.py`)
- Sandboxed subprocess execution with allowlist
- Allowed jobs: verify_dir_exists, validate_jsonl_file
- Timeout constraints: 1-30 seconds
- Security: No arbitrary command execution

### Backend Worker (`worker/backend_worker.py`)
- Main daemon loop polling Redis/memory queue
- Patch validation: size (1000 lines), sensitivity markers, workflow restrictions
- Repository cloning, patching, test execution
- Exponential backoff on empty polls

### MCP Server (`mcp_server/app.py`)
- LLM provider abstraction (OpenAI, Anthropic, Google, OpenRouter)
- Endpoints: `/providers`, `/tools/call`, `/a2a/invoke`
- Bearer token authentication (optional)
- Tool: `mea_ci_guardrail` for patch safety validation

### iRacing Stream Adapter (`ingest/iracing_stream.py`)
- Live telemetry ingestion from iRacing simulator
- Windows-only (requires pyirsdk)
- 60 Hz sampling default, customizable channel mapping
- Generates TelemetryFrame objects

---

## Code Quality Assessment

### Strengths
- ✅ Type hints throughout with Pydantic v2
- ✅ CI/CD checks: ruff linting, mypy type checking, pytest coverage
- ✅ Strong versioning discipline (kernel vs package version)
- ✅ Forensic traceability with append-only ledger
- ✅ Safety-by-default: patch allowlist, guardrails, sensitivity checks
- ✅ Deterministic replay with monotonicity validation

### Weaknesses
- ❌ No root README.md (blocks onboarding)
- ⚠️ `requirements.txt` stale and inconsistent with `pyproject.toml`
- ⚠️ No dependency lock file (Pipfile.lock, poetry.lock, uv.lock)
- ⚠️ Memory queue fallback masks Redis failures
- ⚠️ SQLite ledger on /tmp (non-persistent, world-readable)
- ⚠️ No database connection pooling
- ⚠️ No circuit breaker or retry logic for external services
- ⚠️ Default GITHUB_WEBHOOK_SECRET empty (allows unsigned requests)
- ⚠️ Negative security for patch validation (bans known-bad vs allows known-good)
- ⚠️ No E2E tests, no load tests
- ⚠️ `control_plane/repository.py` likely large with multiple responsibilities

### Known Issues
1. V3.1 had two divergent artifacts with same version → resolved in V3.2 merge
2. Patch size limit (1000 lines) is arbitrary
3. iRacing channel mapping hardcoded
4. ruff/mypy versions not pinned in CI

---

## DevOps & Deployment

### Container Architecture
- **Main App** (`Dockerfile`): python:3-slim, port 8000, gunicorn entrypoint, non-root user
- **Control Plane** (`control_plane/Dockerfile`): Separate service
- **Worker** (`worker/Dockerfile`): Background job processor
- **MCP Server** (`mcp_server/Dockerfile`): LLM provider gateway

### Docker Compose
- `compose.yaml`: Standard Compose with single service
- `compose.debug.yaml`: Debug variant
- `docker-compose.yml`: Legacy file

### GitHub Actions
- **ci.yml**: Linting, type checking, tests on all branches
- **container-build.yml**: Builds three images tagged with commit SHA
- **release-gate.yml**: Version alignment, required CI checks, deploy/publish gates

### Version Management
- **VERSION.json**: kernel_version + package_version + compatibility
- **pyproject.toml**: package version = "0.3.4"
- **CHANGELOG.md**: Must match VERSION.json
- **Release Gate**: Enforces version alignment across all files

---

## Dependencies & External Integrations

### Core Dependencies
- fastapi>=0.115.0, uvicorn>=0.30.0
- pydantic>=2.8.0, psycopg>=3.2.0, redis>=5.0.0
- httpx, PyJWT, cryptography, typer, PyYAML
- **Dev:** pytest, pytest-cov, ruff, mypy

### External Services
- **GitHub**: Webhook ingestion + GitHub App OAuth (HMAC-SHA256)
- **LLM Providers**: OpenAI, Anthropic, Google, OpenRouter (API keys via env vars)
- **iRacing**: Windows-only native IPC to simulator
- **PostgreSQL**: Primary data store (jobs, traces, receipts, webhooks)
- **Redis**: Optional cache/queue (fallback to memory)
- **SQLite**: Session audit ledger

---

## Current State Observations

### Architectural Strengths
- Clear module boundaries with dependency injection
- Strong forensic traceability (append-only ledger with state hashing)
- Deterministic replay capability with validation
- Type safety with Pydantic throughout
- Well-documented versioning and release semantics

### Critical Gaps
1. **Documentation**: Missing README, deployment guide, API docs
2. **Dependency Management**: pyproject.toml vs requirements.txt mismatch, no lock file
3. **Operational Readiness**: No connection pooling, circuit breakers, or graceful degradation
4. **Security**: Default empty webhook secret, negative security model for patches
5. **Testing**: No E2E tests, no load testing, no mocking infrastructure
6. **Code Organization**: repository.py likely has multiple concerns, no custom error types

---

## Key Recommendations

### 1. **Documentation Overhaul (HIGH)**
**Actions:**
- Create README.md with architecture diagram, quick-start, Docker deployment
- Create docs/DEPLOYMENT.md with production checklist, env vars, scaling guide
- Add API docstrings for FastAPI endpoints (Swagger generation)
- Create docs/CONTRIBUTING.md with dev workflow

**Impact:** Reduces onboarding time, enables contributions, eases incident response

### 2. **Dependency Management (HIGH)**
**Actions:**
- Delete requirements.txt; use pyproject.toml as source of truth
- Add lock file (uv pip compile or pip-tools)
- Pin CI versions: ruff==X.Y.Z, mypy==X.Y.Z
- Add CI check: pip-compile --check to verify lock file consistency

**Impact:** Reproducible builds, reduced "works on my machine" errors, security traceability

### 3. **Operational Hardening (MEDIUM)**
**Actions:**
- Add PostgreSQL connection pooling (psycopg_pool)
- Add circuit breaker for Redis (fail-fast, no silent fallback)
- Move SQLite ledger from /tmp to /var/lib/mea/
- Enforce GITHUB_WEBHOOK_SECRET in production
- Add rate limiting middleware (slowapi)

**Impact:** Graceful degradation, prevents data loss, reduces operational surprises

---

## Review Focus Priority

### HIGH (Start Here)
1. **Architecture Review**: `supervisor-loop.md` → `control_plane/app.py` → services
2. **Security Audit**: Patch validation, API auth, secrets management
3. **Dependency Audit**: Resolve pyproject.toml vs requirements.txt
4. **Documentation**: Block review checklist on README completion

### MEDIUM (Secondary)
5. **Test Coverage**: E2E tests, load tests, API mocks
6. **Database Schema**: Verify migration ordering and constraints
7. **Error Handling**: Custom exception hierarchy
8. **MCP Integration**: LLM provider isolation

### LOW (Polish)
9. **Code Style**: Already covered by ruff
10. **Logging/Telemetry**: Not critical for safety
11. **iRacing Adapter**: Platform-specific, low core impact

---

## Summary

The **Motorsport Engineering Agent** is a well-architected system with strong versioning, forensic traceability, and safety-by-default. However, it requires **documentation** and **operational hardening** before confident production deployment.

**Immediate actions:**
✅ Create README + deployment docs  
✅ Fix dependency versioning (lock file)  
✅ Harden DB/cache connectivity  
✅ Security audit of patch validation  

**System excels at:**
- CI/CD automation, multi-stage approvals, audit trail compliance, LLM-driven decisions

**Risks to mitigate:**
- Silent failure modes, undocumented operational requirements, dependency drift

---

*Assessment completed: 2026-04-04*