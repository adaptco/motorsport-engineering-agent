# Product Requirements Document (PRD)
## Motorsport Engineering Agent - Comprehensive Codebase Review

**Document Version:** 1.0  
**Last Updated:** 2026-04-04  
**Status:** NOT READY FOR PRODUCTION (RED blockers identified)  
**Framework:** Ralph Loop Executor-Reviewer Model

---

## 1. Executive Summary

### Project
**Motorsport Engineering Agent - Codebase Production Readiness Review**

### Objective
Conduct a comprehensive review of the motorsport engineering agent codebase to assess production readiness across seven key domains: architecture, security, testing, dependencies, documentation, database operations, and type safety.

### Current Status
🔴 **NOT READY FOR PRODUCTION** - RED blockers identified in documentation and database operational readiness

**Key Findings:**
- ❌ Missing root README.md (blocks onboarding)
- ❌ SQLite ledger on /tmp (non-persistent, security risk)
- ❌ No deployment guide or operational runbook
- ⚠️ Dependency management misaligned (requirements.txt vs pyproject.toml)
- ⚠️ No database connection pooling
- ⚠️ No circuit breakers for external services
- ✅ Strong: Type safety (full mypy), versioning discipline, forensic traceability

### Expected Outcome
- Detailed findings report across 7 domains (RED/YELLOW/GREEN assessment)
- Actionable remediation steps for all RED blockers
- Prioritized roadmap for YELLOW items
- Clear path to production readiness with timeline

---

## 2. Review Scope

### In Scope ✅
- **Architecture Validation**: Component boundaries, dependency graphs, integration patterns
- **Security Audit**: Patch validation logic, webhook HMAC verification, secrets management, input validation
- **Test Coverage Assessment**: Unit, integration, E2E coverage; test infrastructure quality
- **Dependency Management Review**: Source-of-truth alignment, lock file strategy, version consistency
- **Documentation Completeness**: README, API docs, deployment guide, code comments, runbooks
- **Database Operational Readiness**: Schema migrations, connection pooling, persistence strategy, transaction handling
- **Type Safety Verification**: mypy configuration, coverage percentage, dynamic code flagging
- **Operational Hardening**: Health checks, circuit breakers, error handling, graceful degradation

### Out of Scope ❌
- iRacing platform-specific bugs or tuning
- Performance optimization (benchmarking, profiling)
- Cosmetic code style issues (covered by ruff linter)
- Infrastructure provisioning (AWS, GCP, deployment systems)
- Feature roadmap planning

---

## 3. Success Criteria

### Acceptance Criteria for Full Review Completion
- [ ] **All 7 review domains completed** with clear findings and recommendations
- [ ] **RED blockers documented** with specific remediation steps and priority
- [ ] **YELLOW items prioritized** into actionable sprints with owners
- [ ] **Detailed findings report** generated (REVIEW_REPORT.md)
- [ ] **GREEN domains confirmed** with no regression risks
- [ ] **Recommendations documented** for all components with implementation guidance
- [ ] **Clear production readiness path** established with timeline and checkpoints

### Definition of Done
A domain is considered **COMPLETE** when:
1. All files/directories in scope have been reviewed
2. Findings documented with specific code examples or file references
3. Decision criteria applied (GREEN/YELLOW/RED) with justification
4. Recommendations include concrete action items and code snippets where applicable
5. Review findings committed to repository with proper documentation

---

## 4. Detailed Review Tasks

### Task-001: Architecture Validation

**Objective:** Validate system architecture, component design, and integration patterns to ensure sound foundation for production deployment

**Scope:** 
- `control_plane/` - FastAPI orchestration hub
- `worker/` - Background job processor
- `mcp_server/` - LLM provider gateway
- `ingest/` - Data adapters
- `mea/` - Core reasoning engine
- `shared/` - Cross-service utilities
- `docs/supervisor-loop.md` - Architecture reference

**Acceptance Criteria:**
- [ ] Component boundaries documented and verified
- [ ] Dependency graph created (no circular dependencies)
- [ ] Integration points between components identified
- [ ] Data flow through the system mapped
- [ ] Service communication patterns validated
- [ ] Scalability patterns assessed
- [ ] Decision: Architecture is sound (GREEN/YELLOW/RED) with justification
- [ ] Findings documented in architecture section of review report

**Key Files to Review:**
- `docs/supervisor-loop.md` - Supervisor loop architecture
- `control_plane/app.py` - Main application with routers
- `worker/backend_worker.py` - Worker loop implementation
- `mea/policy_engine.py` - Decision engine logic
- `shared/forensic_ledger.py` - Audit trail architecture

**DMN Decision Criteria:**
- Component isolation: Are responsibilities clearly separated?
- Coupling: Are there circular dependencies?
- Scalability: Can components scale independently?
- Failure isolation: Do failures in one component cascade?

**Expected Deliverables:**
- Architecture diagram or graph visualization
- Component interaction matrix
- Potential bottlenecks or risks identified
- Recommendations for architectural improvements

---

### Task-002: Security Audit

**Objective:** Assess security posture including authentication, secrets management, patch validation, and vulnerability controls

**Scope:**
- All authentication and authorization mechanisms
- Webhook HMAC verification (`control_plane/webhooks.py`)
- Patch validation logic (`worker/backend_worker.py`, `control_plane/services/job_runner.py`)
- Secrets and credential handling
- Input validation strategies
- API security (`mcp_server/`)
- GitHub App integration

**Acceptance Criteria:**
- [ ] Patch allowlist validation logic reviewed (size limits, sensitivity markers, workflow restrictions)
- [ ] Webhook HMAC-SHA256 verification confirmed in code
- [ ] Webhook secret requirement enforcement verified (GITHUB_WEBHOOK_SECRET)
- [ ] No hardcoded secrets found in code repository
- [ ] Environment variable usage pattern validated
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] GitHub App authentication flow reviewed
- [ ] Bearer token authentication for MCP server verified
- [ ] Input validation for all API endpoints assessed
- [ ] Decision: Security posture (GREEN/YELLOW/RED) with specific vulnerabilities or strengths noted

**Key Files to Review:**
- `control_plane/webhooks.py` - GitHub webhook HMAC validation
- `worker/backend_worker.py` - Patch validation logic
- `control_plane/services/job_runner.py` - Sandboxed execution allowlist
- `mcp_server/app.py` - Bearer token authentication
- `worker/github_app_client.py` - GitHub App auth
- `shared/models.py` - Input validation with Pydantic
- `.env.example` - Secrets documentation

**DMN Decision Criteria:**
- Are secrets properly externalized (no hardcoding)?
- Is webhook validation cryptographically sound?
- Is patch validation comprehensive (allowlist-based)?
- Are API endpoints properly authenticated?
- Is SQL injection prevention in place?

**Expected Deliverables:**
- Vulnerability assessment with severity levels
- Security control verification checklist
- Recommendations for patch validation improvements
- Guidelines for secret rotation and credential management

---

### Task-003: Test Coverage Assessment

**Objective:** Evaluate test infrastructure, coverage metrics, and quality of test implementation across unit, integration, and end-to-end tests

**Scope:**
- `tests/` directory - All test files
- `.github/workflows/ci.yml` - CI/CD testing pipeline
- Test coverage metrics and reports
- Mock strategy and fixtures
- Test data and seeding

**Acceptance Criteria:**
- [ ] Test types identified and categorized (unit, integration, E2E, performance)
- [ ] Overall test coverage percentage determined and documented
- [ ] Coverage gaps identified and prioritized
- [ ] E2E test strategy assessed (present/missing/incomplete)
- [ ] Mock infrastructure evaluated (fixtures, conftest.py patterns)
- [ ] Critical path E2E tests verified (webhook → job → result)
- [ ] Test flakiness assessment completed
- [ ] CI test execution time profiled
- [ ] Decision: Test readiness (GREEN/YELLOW/RED) with coverage details

**Key Files to Review:**
- `tests/` - All test files
- `tests/conftest.py` - Fixtures and shared setup
- `.github/workflows/ci.yml` - CI testing stage
- `pytest.ini` or `pyproject.toml` - Test configuration
- `.coverage` - Coverage report

**DMN Decision Criteria:**
- What is unit test coverage? (Target: ≥85%)
- Are integration tests covering DB/external service interactions?
- Is critical path covered by E2E tests?
- Are mocks properly configured?
- Is test execution deterministic (no flakiness)?

**Expected Deliverables:**
- Coverage report with per-module breakdown
- List of untested critical paths
- E2E test strategy recommendations
- Test infrastructure improvements (mock patterns, fixtures)

---

### Task-004: Dependency Management Review

**Objective:** Validate dependency declarations, versions, and consistency; establish single source of truth for package management

**Scope:**
- `pyproject.toml` - Primary dependency specification
- `requirements.txt` - Current dependency pinning (if exists)
- Lock file strategy (uv.lock, poetry.lock, requirements.lock)
- CI tool versions (ruff, mypy, pytest)
- Transitive dependency analysis

**Acceptance Criteria:**
- [ ] Source of truth identified (pyproject.toml vs requirements.txt)
- [ ] Version inconsistencies between files documented
- [ ] Lock file strategy recommended or implemented
- [ ] CI tool versions pinned in workflow files
- [ ] Dependency security audit performed (pip-audit or equivalent)
- [ ] License compatibility verified for all dependencies
- [ ] Transitive dependencies reviewed for bloat or conflicts
- [ ] Python version constraints validated
- [ ] Optional dependencies (dev, extras) organized properly
- [ ] Decision: Dependency management (GREEN/YELLOW/RED) with action items

**Key Files to Review:**
- `pyproject.toml` - Main dependency source
- `requirements.txt` - Legacy requirements file
- `.github/workflows/ci.yml` - CI tool version specifications
- `pyproject.toml [tool.poetry]` or `[project]` - Dependency sections

**DMN Decision Criteria:**
- Is there a single source of truth?
- Are versions locked or pinned appropriately?
- Are there CVE vulnerabilities in dependencies?
- Do license constraints apply?
- Is there dependency version drift between environments?

**Expected Deliverables:**
- Dependency audit report with CVE assessment
- Recommendation to eliminate requirements.txt or use as lock file
- Lock file generation command/strategy
- CI workflow update recommendations (pin tool versions)

---

### Task-005: Documentation Audit

**Objective:** Assess documentation completeness, quality, and usability for developers, operators, and contributors

**Scope:**
- `README.md` - Root repository documentation
- `docs/` - Architecture and deployment guides
- API documentation (FastAPI docstrings)
- Code comments (docstrings, inline comments)
- Deployment procedures and runbooks
- Contributing guidelines
- Configuration documentation

**Acceptance Criteria:**
- [ ] README.md completeness checked (exists, includes architecture, quick-start, Docker, contributing link)
- [ ] Architecture documentation verified (supervisor-loop.md, component descriptions)
- [ ] Deployment guide documented or missing flagged (env vars, database setup, scaling)
- [ ] API documentation completeness assessed (FastAPI endpoint docstrings with examples)
- [ ] Code comments quality evaluated (adequate explanation of complex logic)
- [ ] Missing documentation gaps identified with priority
- [ ] Configuration documentation (env vars in .env.example)
- [ ] Runbook for common operations documented or flagged
- [ ] Decision: Documentation readiness (GREEN/YELLOW/RED) with gaps

**Key Files to Review:**
- `README.md` - Root documentation (or note if missing)
- `docs/supervisor-loop.md` - Architecture reference
- `docs/` - All documentation files
- `control_plane/app.py` - API endpoint docstrings
- `mcp_server/app.py` - LLM provider documentation
- `.env.example` - Configuration documentation
- `CONTRIBUTING.md` - (if exists)

**DMN Decision Criteria:**
- Does README exist and cover architecture, quick-start, Docker?
- Are API endpoints documented with examples?
- Is deployment process documented?
- Are env vars documented in .env.example?
- Is contributing process documented?

**Expected Deliverables:**
- Documentation completeness assessment report
- README template or improvements if needed
- Missing documentation checklist with priority
- Documentation structure recommendations

---

### Task-006: Database & State Management Review

**Objective:** Validate database schema, migrations, connection pooling, persistence strategy, and transaction handling for production readiness

**Scope:**
- Database schema and migrations (`db/migrations/`)
- Connection pooling strategy
- Transaction handling and ACID compliance
- Forensic ledger persistence (`shared/forensic_ledger.py`)
- Database configuration (`control_plane/config.py`, `shared/db.py`)
- State management patterns

**Acceptance Criteria:**
- [ ] Migration strategy reviewed and documented
- [ ] Migration files verified with UP and DOWN steps
- [ ] Schema evolution tested locally
- [ ] Forensic ledger persistence verified (NOT on /tmp, durable storage)
- [ ] Connection pooling requirements identified or missing flagged
- [ ] Transaction handling reviewed for ACID compliance
- [ ] Backup and restore procedures documented or flagged
- [ ] Database constraints verified (foreign keys, unique, check)
- [ ] Indexes reviewed for query performance
- [ ] State management patterns validated
- [ ] Decision: Database readiness (GREEN/YELLOW/RED) with specific issues

**Key Files to Review:**
- `db/migrations/` - All migration files
- `shared/forensic_ledger.py` - Ledger implementation and storage location
- `shared/db.py` - Database connection setup
- `control_plane/config.py` - Database configuration
- `control_plane/repository.py` - Database query patterns
- `pyproject.toml` - Database dependency versions

**DMN Decision Criteria:**
- Are migrations versioned and reversible?
- Is connection pooling implemented?
- Is ledger persistence durable (not /tmp)?
- Are transactions properly handled?
- Are queries parameterized?

**Expected Deliverables:**
- Database readiness assessment
- Migration strategy recommendations
- Connection pooling implementation guidance
- Ledger persistence fix (if on /tmp)
- Backup/restore procedure recommendations

---

### Task-007: Operational Hardening Assessment

**Objective:** Evaluate production readiness for monitoring, error handling, graceful degradation, and observability

**Scope:**
- Health check endpoints (`control_plane/routes/`, `mcp_server/`)
- Error handling patterns throughout codebase
- Circuit breaker patterns for external services
- Graceful degradation strategies
- Logging and observability
- Rate limiting and throttling
- Timeout and retry logic

**Acceptance Criteria:**
- [ ] Health check endpoints identified (`/healthz` coverage)
- [ ] Health check response format verified (includes all critical services)
- [ ] Circuit breaker patterns assessed for Redis, PostgreSQL, external APIs
- [ ] Error handling strategy reviewed (specific exception types, logging)
- [ ] Graceful degradation tested (Redis fallback to memory, etc.)
- [ ] Timeout values documented for external service calls
- [ ] Retry logic and exponential backoff implemented
- [ ] Logging coverage evaluated (request IDs, structured logging)
- [ ] Rate limiting implemented for public endpoints
- [ ] Monitoring/metrics strategy identified
- [ ] Decision: Operational readiness (GREEN/YELLOW/RED) with hardening gaps

**Key Files to Review:**
- `control_plane/routes/` - API endpoints including `/healthz`
- `control_plane/queue.py` - Redis fallback and error handling
- `control_plane/services/` - Service layer error handling
- `worker/backend_worker.py` - Worker error handling and retry logic
- `mcp_server/app.py` - External API call error handling
- `shared/db.py` - Database connection error handling
- `control_plane/config.py` - Timeout and retry configuration

**DMN Decision Criteria:**
- Do health checks cover all critical dependencies?
- Are external service failures handled gracefully?
- Is retry logic with backoff in place?
- Is logging comprehensive and structured?
- Are rate limits implemented?

**Expected Deliverables:**
- Operational hardening report
- Health check verification and improvements
- Circuit breaker implementation recommendations
- Error handling improvements checklist
- Monitoring and observability strategy

---

### Task-008: Type Safety Verification

**Objective:** Validate type checking coverage, correctness, and identify any unchecked dynamic code patterns

**Scope:**
- mypy configuration and CI integration
- Type hints coverage across codebase
- Pydantic model type definitions
- Dynamic code patterns (if any)
- Type ignore comments and justification
- Generic type usage (List, Dict, Optional)

**Acceptance Criteria:**
- [ ] mypy coverage percentage determined from CI
- [ ] mypy configuration reviewed (`pyproject.toml` [tool.mypy])
- [ ] Type errors documented (if any exist)
- [ ] Type ignore comments reviewed and justified
- [ ] Unchecked dynamic code flagged and evaluated
- [ ] Generic types properly parameterized
- [ ] Pydantic models verified for type safety
- [ ] Union types and Optional handled correctly
- [ ] mypy strictness level documented (--strict or partial)
- [ ] Decision: Type safety level (GREEN/YELLOW/RED) with assessment

**Key Files to Review:**
- `pyproject.toml` - mypy configuration
- `.github/workflows/ci.yml` - mypy execution in CI
- `shared/models.py` - Pydantic model definitions
- `control_plane/` - Main application type coverage
- `worker/` - Worker type coverage
- `mea/` - Reasoning engine type coverage

**DMN Decision Criteria:**
- What is the mypy coverage %? (Target: 100% with --strict or clear baseline)
- Are there any type: ignore comments without justification?
- Are Pydantic models properly typed?
- Is dynamic code minimized?

**Expected Deliverables:**
- Type safety assessment report
- mypy configuration recommendations
- Coverage metrics and gaps
- Recommendations for improving type safety

---

## 5. DMN Integration Framework

### Decision Mapping

Each task produces a **decision output** mapped to the DMN (Decision Management Network) framework:

| Task | Domain | Input Criteria | Output Decision | Risk Level |
|------|--------|----------------|-----------------|-----------|
| Task-001 | Architecture | Component boundaries, dependency graph, scalability | SOUND / NEEDS_REFACTOR | GREEN/YELLOW/RED |
| Task-002 | Security | Vulnerability findings, auth verification, secrets audit | SECURE / ISSUES_FOUND | GREEN/YELLOW/RED |
| Task-003 | Testing | Coverage %, test types, E2E coverage | ADEQUATE / GAPS | GREEN/YELLOW/RED |
| Task-004 | Dependencies | Version alignment, lock file, CVEs | MANAGED / DRIFT | GREEN/YELLOW/RED |
| Task-005 | Documentation | README, API docs, deployment guide | COMPLETE / INCOMPLETE | GREEN/YELLOW/RED |
| Task-006 | Database | Migrations, pooling, persistence, transactions | READY / HARDENING_NEEDED | GREEN/YELLOW/RED |
| Task-007 | Operational | Health checks, circuit breakers, error handling | HARDENED / GAPS | GREEN/YELLOW/RED |
| Task-008 | Type Safety | mypy %, type errors, type ignores | SAFE / PARTIAL | GREEN/YELLOW/RED |

### Escalation Path for RED Items

**RED Blockers** must be addressed before production deployment:

1. **Immediate (Day 1-2)**: Document RED findings with remediation steps
2. **Prioritization (Day 3)**: Manager approval for remediation plan
3. **Implementation (Sprint)**: Assign owners and track completion
4. **Verification (Before Merge)**: Reviewer confirms RED → YELLOW/GREEN
5. **Deployment Gate**: All RED items resolved before production approval

---

## 6. Deliverables

### Each Task Produces

1. **Findings Report**
   - Detailed assessment of the review area
   - Code examples or file references for issues
   - Strengths and weaknesses identified

2. **Risk Assessment**
   - RED/YELLOW/GREEN classification with justification
   - Severity and impact analysis
   - Business/technical impact of issues

3. **Actionable Recommendations**
   - Specific remediation steps
   - Code snippets or file changes where applicable
   - Implementation priority and estimated effort
   - Ownership assignment

4. **Acceptance Criteria Verification**
   - Checkmarks for each criterion completed
   - Evidence or references for each finding
   - Notes on any items that could not be verified

### Final Deliverables (End of Review)

1. **REVIEW_REPORT.md** - Comprehensive findings across all 7 domains
2. **PROGRESS.md** - Task completion status and tracking
3. **Commit with Findings** - All review documentation committed to repository
4. **Production Readiness Summary** - Clear GO/NO-GO decision with timeline

---

## 7. Success Timeline & Execution

### Task Execution Model

**All tasks are INDEPENDENT and can run in PARALLEL:**
- Task-001 (Architecture) ⫶ Independent
- Task-002 (Security) ⫶ Independent  
- Task-003 (Testing) ⫶ Independent
- Task-004 (Dependencies) ⫶ Independent
- Task-005 (Documentation) ⫶ Independent
- Task-006 (Database) ⫶ Independent
- Task-007 (Operational) ⫶ Independent
- Task-008 (Type Safety) ⫶ Independent

**Execution Timeline:**
- **Estimated Duration**: 2-5 days (depending on executor availability and findings complexity)
- **Parallel Execution**: All 8 tasks can be worked simultaneously by different reviewers
- **Sequential Only**: DMN decision consolidation and production readiness conclusion

### Review Checkpoint Gates

| Phase | Gate | Criteria | Owner |
|-------|------|----------|-------|
| **Phase 1: Initial Review** (Days 1-2) | All tasks complete | All 8 tasks submitted findings | Executor |
| **Phase 2: DMN Evaluation** (Day 3) | Risk assessment | GREEN/YELLOW/RED decisions on each domain | Reviewer |
| **Phase 3: Remediation Plan** (Days 4-5) | Action items prioritized | RED blockers have remediation owners and timeline | Manager |
| **Phase 4: Production Ready** | Final gate | All RED resolved, YELLOW prioritized, deployment approval | Engineering Lead |

---

## 8. Acceptance Criteria for PRD Completion

The PRD is considered **COMPLETE** and ready for Ralph Loop execution when:

- [ ] **8 Review Tasks Defined** with clear scope, acceptance criteria, and deliverables
- [ ] **Each Task Includes**: Specific files to review, DMN decision criteria, expected outputs
- [ ] **Success Criteria Documented** for overall review completion
- [ ] **Deliverables Specified** for each task and overall review
- [ ] **Execution Model Clear** (parallel tasks, checkpoint gates, timeline)
- [ ] **DMN Integration** references included in each task
- [ ] **Risk Assessment Framework** defined (RED/YELLOW/GREEN)
- [ ] **Scope Clearly Defined** (in scope/out of scope)
- [ ] **PRD.md and PROGRESS.md Files** created and committed

---

## 9. References

### Key Documents
- `.github/codebase-assessment.md` - Detailed technical assessment
- `.github/dmn-manager-decisions.md` - Decision management framework
- `.github/review-checklist.md` - Practical review checklist
- `docs/supervisor-loop.md` - Architecture documentation
- `VERSION.json` - Version tracking (kernel + package)

### Related Requirements
- Python 3.11+ for type safety validation
- PostgreSQL for database review
- Redis for cache/queue patterns
- FastAPI/Uvicorn for HTTP endpoint verification

### Success Metrics
- **Production Ready**: All domains GREEN or YELLOW with mitigation plans
- **NOT Ready**: Any RED domain blocks deployment
- **Documentation**: README, deployment guide, API docs completed
- **Security**: No vulnerabilities or misconfigurations
- **Testing**: ≥85% coverage, critical path E2E tested

---

**Document Status:** READY FOR RALPH LOOP EXECUTION  
**Version:** 1.0  
**Last Updated:** 2026-04-04  
**Next Steps:** Execute Task-001 through Task-008 in parallel; consolidate findings in REVIEW_REPORT.md

---

## Tasks (Original - Keep for reference)

### Task-001: Analyze Project Structure and Configuration

**Priority**: High
**Estimated Iterations**: 1-2

**Acceptance Criteria**:
- [ ] Project dependencies and versions documented (from pyproject.toml)
- [ ] Docker configuration reviewed (Dockerfile, compose files)
- [ ] Database schema understood (migrations/)
- [ ] Configuration files analyzed (configs/, VERSION.json)
- [ ] Build and deployment scripts reviewed (Makefile, scripts/)

**Verification**:
```bash
# Check if project builds successfully
make build
# Verify Docker images can be built
docker build -t mea-test .
```

### Task-002: Review Control Plane Architecture

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Main FastAPI application structure documented (control_plane/app.py)
- [ ] API routes analyzed (agent, replay, session, verifier, github)
- [ ] Job management system understood (queue.py, repository.py)
- [ ] Webhook integrations reviewed (github_app.py, webhooks.py)
- [ ] Health check endpoints verified

**Verification**:
```bash
# Test control plane health endpoint
curl http://localhost:8000/healthz
# Verify API routes are accessible
python -c "from control_plane.app import app; print('Routes loaded successfully')"
```

### Task-003: Examine MCP Server Implementation

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] MCP server purpose and role documented
- [ ] Supported LLM providers identified (OpenAI, Anthropic, Google, OpenRouter)
- [ ] Tool implementations reviewed (mea_ci_guardrail)
- [ ] Authentication mechanisms understood
- [ ] A2A invoke functionality analyzed

**Verification**:
```bash
# Check MCP server health
curl http://localhost:8001/healthz
# Verify providers endpoint
curl http://localhost:8001/providers
```

### Task-004: Analyze Worker Backend Processing

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Worker loop logic documented (backend_worker.py)
- [ ] Job processing pipeline understood
- [ ] GitHub integration reviewed (github_app_client.py)
- [ ] Patch validation mechanisms analyzed
- [ ] Error handling and logging reviewed

**Verification**:
```bash
# Test worker can import without errors
python -c "from worker.backend_worker import worker_loop; print('Worker imports successfully')"
# Verify GitHub client functionality (requires token)
python -c "from worker.github_app_client import get_installation_token; print('GitHub client available')"
```

### Task-005: Review Telemetry Ingestion System

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] iRacing integration documented (iracing_stream.py)
- [ ] Telemetry data models understood (shared/models.py)
- [ ] Data streaming mechanisms analyzed
- [ ] Channel mapping and sampling reviewed
- [ ] Error handling for simulator unavailability

**Verification**:
```bash
# Test telemetry models can be imported
python -c "from shared.models import TelemetryFrame, ReplayMetrics; print('Models import successfully')"
# Verify iRacing stream adapter (without live simulator)
python -c "from ingest.iracing_stream import load_pyirsdk; print('iRacing adapter available')"
```

### Task-006: Examine AI Agent and Reasoning Components

**Priority**: High
**Estimated Iterations**: 3-4

**Acceptance Criteria**:
- [ ] Agent decision API reviewed (routes/agent.py)
- [ ] Reasoning engine analyzed (mea/reasoning/)
- [ ] Policy engine functionality understood
- [ ] Time domain handling reviewed
- [ ] Supervisor loop documented

**Verification**:
```bash
# Test agent routes import
python -c "from control_plane.routes.agent import router; print('Agent routes available')"
# Verify reasoning components
python -c "from mea.reasoning.policy_engine import PolicyEngine; print('Policy engine available')"
```

### Task-007: Analyze Data Persistence and Storage

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Database models reviewed (shared/models.py)
- [ ] Migration scripts analyzed (db/migrations/)
- [ ] Forensic ledger functionality understood
- [ ] Session receipts and evidence packets reviewed
- [ ] Data validation mechanisms examined

**Verification**:
```bash
# Test database connection (requires running DB)
python -c "from shared.db import get_db; print('DB module available')"
# Verify forensic ledger
python -c "from shared.forensic_ledger import ForensicLedger; print('Ledger available')"
```

### Task-008: Review Testing and Quality Assurance

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Test structure analyzed (tests/ directory)
- [ ] Unit and integration tests reviewed
- [ ] Test coverage assessed
- [ ] CI/CD guardrails examined (mea_ci_guardrail.py)
- [ ] Validation utilities understood (jsonl_validator.py)

**Verification**:
```bash
# Run test suite
pytest --collect-only
# Check test coverage
pytest --cov=shared --cov-report=term-missing
```

### Task-009: Document Data Flow and Architecture

**Priority**: High
**Estimated Iterations**: 3-4

**Acceptance Criteria**:
- [ ] End-to-end data flow mapped (telemetry → processing → decisions)
- [ ] Component interaction diagram created
- [ ] API communication patterns documented
- [ ] Job lifecycle traced
- [ ] External integrations mapped (GitHub, iRacing, LLM providers)

**Verification**:
```bash
# Verify all components can be imported together
python -c "
from control_plane.app import app
from mcp_server.app import app as mcp_app
from worker.backend_worker import worker_loop
from ingest.iracing_stream import stream_iracing_frames
print('All main components import successfully')
"
```

### Task-010: Identify Key Features and Capabilities

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Core features documented (CI fixing, replay analysis, session management)
- [ ] AI decision-making capabilities listed
- [ ] Telemetry processing features identified
- [ ] GitHub integration features reviewed
- [ ] Performance metrics and monitoring understood

**Verification**:
```bash
# Review metrics configuration
cat metrics/performance_tasks.yaml
# Check release manifest
cat release/RELEASE_MANIFEST.json
```

### Task-011: Assess Technology Stack and Dependencies

**Priority**: Low
**Estimated Iterations**: 1-2

**Acceptance Criteria**:
- [ ] Python version and key libraries documented
- [ ] Infrastructure dependencies identified (Redis, PostgreSQL)
- [ ] External API integrations listed
- [ ] Development tools and frameworks reviewed

**Verification**:
```bash
# Check Python version compatibility
python --version
# Verify key dependencies
python -c "import fastapi, uvicorn, pydantic, psycopg, redis; print('Core dependencies available')"
```

### Task-012: Create Comprehensive Review Report

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:
- [ ] Executive summary of system purpose
- [ ] Architecture overview with diagrams
- [ ] Component descriptions and responsibilities
- [ ] Key workflows documented
- [ ] Technology assessment
- [ ] Recommendations for improvements
- [ ] Security considerations noted

**Verification**:
```bash
# Create review report file
echo "# MEA Codebase Review Report" > REVIEW_REPORT.md
echo "Report created successfully"
```

## Technical Constraints
- Language: Python 3.11+
- Framework: FastAPI for web services
- Database: PostgreSQL with psycopg
- Cache: Redis
- External APIs: GitHub API, iRacing SDK, LLM providers
- Testing: pytest with coverage
- Containerization: Docker

## Architecture Notes
- Microservices architecture with separate control plane, MCP server, and worker
- Event-driven job processing with queue system
- AI agent integration for decision making in motorsport context
- Forensic ledger for audit trails and evidence collection
- GitHub App integration for CI/CD automation

## Out of Scope
- Detailed performance benchmarking
- Security vulnerability assessment
- Production deployment configuration
- User interface components (if any)
- Third-party LLM provider implementations