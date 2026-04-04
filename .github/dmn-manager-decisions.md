# DMN: Manager Decision Model for Code Review & Deployment Readiness

**Document Version:** 1.0  
**Last Updated:** 2026-04-04  
**Domain:** Motorsport Engineering Agent (Python 3.11+ FastAPI System)  
**Audience:** Senior Engineering Managers, Architects, Code Reviewers

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Decision Structure & Hierarchy](#decision-structure--hierarchy)
3. [Risk Scoring Framework](#risk-scoring-framework)
4. [Decision Tables by Domain](#decision-tables-by-domain)
5. [Top-Level Decision Logic](#top-level-decision-logic)
6. [Manager Decision Rules & Policies](#manager-decision-rules--policies)
7. [Escalation & Waiver Protocol](#escalation--waiver-protocol)
8. [Implementation Guidance](#implementation-guidance)

---

## Executive Summary

This Decision Model encodes how engineering leadership evaluates **code readiness for review, merge, and production deployment** across seven key domains:

| Domain | Current Status | Risk Level |
|--------|----------------|-----------|
| **Documentation** | Missing core docs | 🔴 RED |
| **Dependencies** | Misaligned (txt vs toml) | 🟡 YELLOW |
| **Security** | Partial enforcement | 🟡 YELLOW |
| **Testing** | Unit + integration, no E2E | 🟡 YELLOW |
| **Database** | No connection pooling | 🟡 YELLOW |
| **Type Safety** | Full mypy coverage | 🟢 GREEN |
| **Operational Hardening** | Missing circuit breakers | 🟡 YELLOW |

**Decision:** **Not Ready for Production Deployment** (Blocker: RED documentation gap)  
**Action:** Address RED items before code review approval. Schedule YELLOW items for next sprint.

---

## Decision Structure & Hierarchy

```
┌─────────────────────────────────────────────────┐
│ TOP-LEVEL DECISION:                             │
│ "Is Codebase Ready for Production Deployment?"  │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────┴─────────────┬──────────────────┬──────────────┬──────────────┬────────────────┐
    │                          │                  │              │              │                │
    ▼                          ▼                  ▼              ▼              ▼                ▼
┌─────────────┐      ┌─────────────────┐   ┌──────────┐  ┌──────────────┐  ┌──────────────┐ ┌──────────────┐
│ARCHITECTURE │      │    SECURITY     │   │ TESTING  │  │  DEPENDENCY  │  │  DATABASE    │ │DOCUMENTATION│
│ ASSESSMENT  │      │     AUDIT       │   │VALIDATION│  │ MANAGEMENT   │  │   READINESS  │ │   QUALITY    │
└─────────────┘      └─────────────────┘   └──────────┘  └──────────────┘  └──────────────┘ └──────────────┘
```

Each sub-decision follows:
- **Inputs**: Specific criteria derived from codebase assessment
- **Decision Logic**: DMN Hit Policy (FIRST or COLLECT)
- **Outputs**: Risk Level (RED/YELLOW/GREEN), recommendation, action items

---

## Risk Scoring Framework

### Risk Levels Definition

| Level | Color | Criteria | Action Required | Timeline |
|-------|-------|----------|-----------------|----------|
| **HIGH RISK** | 🔴 RED | Blocks deployment/review; architectural flaw or security gap | Must fix before approval | Immediate |
| **MEDIUM RISK** | 🟡 YELLOW | Important gap; impacts production reliability or team productivity | Address before release | Next sprint |
| **LOW RISK** | 🟢 GREEN | Minor improvement; technical debt that doesn't impact safety | Can defer | Backlog |

### Aggregation Logic

```
IF any domain = RED
  THEN overall_readiness = "BLOCKED"
  
ELSE IF any domain = YELLOW
  THEN overall_readiness = "CAUTION" (proceed with plan to address YELLOW items)
  
ELSE IF all domains = GREEN
  THEN overall_readiness = "READY_FOR_PRODUCTION"
```

---

## Decision Tables by Domain

### 1. DOCUMENTATION QUALITY

**Scope:** README, deployment guide, API docs, contribution guidelines, runbooks  
**Hit Policy:** COLLECT all findings

| Input | Criterion | Value | Risk | Recommendation |
|-------|-----------|-------|------|-----------------|
| **README.md** | Root repository documentation | ❌ Missing | 🔴 RED | Create immediately; include architecture diagram, quick-start, Docker deployment |
| **DEPLOYMENT.md** | Production deployment guide | ❌ Missing | 🔴 RED | Create: env vars, connection strings, scaling guidelines, disaster recovery |
| **API Documentation** | FastAPI Swagger/OpenAPI | ❌ Auto-generated only | 🟡 YELLOW | Add endpoint docstrings and examples in code |
| **CONTRIBUTING.md** | Developer workflow guide | ❌ Missing | 🟡 YELLOW | Create: PR process, branch naming, commit conventions, local dev setup |
| **Architecture Docs** | System design explanation | ✅ Exists (`docs/supervisor-loop.md`, etc.) | 🟢 GREEN | Maintain and link from README |
| **Database Schema Docs** | Migration and ER diagram | ❌ Missing | 🟡 YELLOW | Document 3 migrations, primary/foreign keys, connection pooling setup |
| **Runbooks** | Incident response procedures | ❌ Missing | 🟡 YELLOW | Create for: DB failover, Redis fallback, webhook replay |

**Decision Rule:**

```
IF README.md MISSING OR DEPLOYMENT.md MISSING
  THEN risk = RED
  ACTION = "Block merge until documentation complete"
  
ELSE IF API docs incomplete OR CONTRIBUTING.md missing
  THEN risk = YELLOW
  ACTION = "Address before next release"
  
ELSE IF architecture docs exist AND complete
  THEN risk = GREEN
  ACTION = "Continue with routine updates"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Blocker**: Documentation gaps prevent confident onboarding
- **Action Items**: 
  - [ ] Create/update README.md
  - [ ] Create/update DEPLOYMENT.md
  - [ ] Add docstring examples to FastAPI routes
  - [ ] Create CONTRIBUTING.md
  - [ ] Document database schema

---

### 2. SECURITY AUDIT

**Scope:** Secret enforcement, API authentication, patch validation, dependency scanning  
**Hit Policy:** FIRST (stop at first HIGH risk)

| Input | Criterion | Current State | Risk | Recommendation |
|-------|-----------|---------------|------|-----------------|
| **Webhook Secret** | `GITHUB_WEBHOOK_SECRET` enforcement | ⚠️ Default empty (allows unsigned) | 🔴 RED | Enforce required in production; validate HMAC-SHA256 on every webhook |
| **Bearer Token Auth** | MCP server token validation | ✅ Present but optional | 🟡 YELLOW | Make required in production; rotate quarterly |
| **Patch Validation** | Allowlist vs blocklist model | ⚠️ Negative security (bans known-bad) | 🟡 YELLOW | Switch to positive security (allows known-good); use AST analysis |
| **Dependency Scanning** | Vulnerability detection | ❌ Not implemented | 🟡 YELLOW | Add: `pip-audit` in CI, GitHub Dependabot alerts |
| **Secret Detection** | `truffleHog` or equivalent | ❌ Not implemented | 🟡 YELLOW | Add pre-commit hook; fail CI on secret detection |
| **API Rate Limiting** | Slowapi or equivalent | ❌ Not implemented | 🟡 YELLOW | Add rate limiting middleware for `/repos/fix-ci` endpoint |
| **Database Encryption** | PostgreSQL SSL/TLS | ❓ Not documented | 🟡 YELLOW | Enforce SSL in `psycopg` connection string |

**Decision Rule:**

```
IF GITHUB_WEBHOOK_SECRET empty OR secrets found in code
  THEN risk = RED
  ACTION = "Block deployment; rotate credentials; scan history"
  
ELSE IF patch validation is negative-model OR no dependency scanning
  THEN risk = YELLOW
  ACTION = "Upgrade to positive-model + scanning before release"
  
ELSE IF bearer token optional OR rate limiting missing
  THEN risk = YELLOW
  ACTION = "Address in next sprint"
  
ELSE
  THEN risk = GREEN
  ACTION = "Security posture acceptable"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Blockers**: Secret leaks, unsigned webhooks
- **Action Items**:
  - [ ] Set `GITHUB_WEBHOOK_SECRET` to random value in production
  - [ ] Add pre-commit hook: `pip install detect-secrets`
  - [ ] Switch patch validation to AST allowlist
  - [ ] Add `pip-audit` to CI pipeline
  - [ ] Enforce bearer token authentication for MCP
  - [ ] Add rate limiting to FastAPI

---

### 3. TEST COVERAGE VALIDATION

**Scope:** Unit, integration, E2E tests; coverage %; test infrastructure  
**Hit Policy:** COLLECT

| Input | Test Type | Coverage | Risk | Recommendation |
|-------|-----------|----------|------|-----------------|
| **Unit Tests** | Fast, isolated tests | ✅ Present (~70-80% estimated) | 🟢 GREEN | Maintain; target 90%+ |
| **Integration Tests** | DB + Redis + services | ✅ Present | 🟢 GREEN | Expand test matrix for edge cases |
| **End-to-End Tests** | Full workflow (webhook → job → completion) | ❌ Missing | 🔴 RED | Create E2E suite; test critical paths |
| **Load Tests** | Performance under 10x traffic | ❌ Missing | 🟡 YELLOW | Create load test suite; identify bottlenecks |
| **Mock Infrastructure** | `pytest-mock`, `responses`, `factory_boy` | ⚠️ Partial | 🟡 YELLOW | Standardize mocking strategy; reduce DB dependency |
| **CI Test Execution** | Runs on PR + main | ✅ Present (ruff, mypy, pytest) | 🟢 GREEN | Maintain; consider parallelization |
| **Coverage Reporting** | `pytest-cov` + coverage threshold | ⚠️ Present but threshold not enforced | 🟡 YELLOW | Add CI check: `coverage report --fail-under=85` |

**Decision Rule:**

```
IF E2E test suite missing
  THEN risk = RED
  ACTION = "Add E2E tests for critical paths before production release"
  
ELSE IF coverage < 80% OR no load tests
  THEN risk = YELLOW
  ACTION = "Schedule for next sprint; track in backlog"
  
ELSE IF coverage >= 85% AND E2E tests pass
  THEN risk = GREEN
  ACTION = "Testing posture acceptable"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Blockers**: No E2E tests for webhook → deployment pipeline
- **Action Items**:
  - [ ] Create E2E test suite (fixtures: webhook → job queue → execution → result)
  - [ ] Add `coverage --fail-under=85` check to CI
  - [ ] Create load test scenario (10x webhook rate)
  - [ ] Document mock strategy for team

---

### 4. DEPENDENCY MANAGEMENT CHECK

**Scope:** Lock files, version pinning, pyproject.toml consistency, vulnerability scanning  
**Hit Policy:** FIRST

| Input | Criterion | Current State | Risk | Recommendation |
|-------|-----------|---------------|------|-----------------|
| **Lock File Present** | `uv.lock` or `poetry.lock` or `Pipfile.lock` | ❌ Missing | 🔴 RED | Generate via `uv pip compile` or `pip-tools` |
| **pyproject.toml vs requirements.txt** | Source of truth alignment | ⚠️ Inconsistent | 🔴 RED | Delete requirements.txt; use pyproject.toml only |
| **CI Tool Versions** | ruff, mypy pinned | ❌ Not pinned | 🟡 YELLOW | Pin in CI: `ruff==0.X.Y`, `mypy==1.X.Y` |
| **Dependency Audit** | `pip-audit` on new deps | ❌ Not in CI | 🟡 YELLOW | Add `pip-audit` step; fail on CRITICAL/HIGH |
| **Python Version** | Explicitly supported versions | ✅ Python 3.11+ | 🟢 GREEN | Maintain and document |
| **Transitive Deps** | Indirect dependencies tracked | ⚠️ Unknown | 🟡 YELLOW | Run `pip tree`; document high-risk transitive deps |

**Decision Rule:**

```
IF lock file missing OR pyproject.toml inconsistent with requirements.txt
  THEN risk = RED
  ACTION = "Block merge; regenerate lock file; delete requirements.txt"
  
ELSE IF CI tool versions not pinned OR pip-audit not in CI
  THEN risk = YELLOW
  ACTION = "Add before release; prevents drift in CI environment"
  
ELSE IF lock file present AND consistent
  THEN risk = GREEN
  ACTION = "Dependencies reproducible"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Blockers**: Inconsistent dependency sources prevent reproducible builds
- **Action Items**:
  - [ ] Delete requirements.txt
  - [ ] Regenerate lock file via `uv pip compile`
  - [ ] Pin CI versions: `ruff`, `mypy` in workflow YAML
  - [ ] Add `pip-audit` CI step
  - [ ] Document dependency governance policy

---

### 5. DATABASE READINESS

**Scope:** Connection pooling, migrations, schema validation, backup strategy  
**Hit Policy:** FIRST

| Input | Criterion | Current State | Risk | Recommendation |
|-------|-----------|---------------|------|-----------------|
| **Connection Pooling** | `psycopg_pool` or equivalent | ❌ Not implemented | 🔴 RED | Add connection pooling; set min=5, max=20 |
| **SQLite Ledger Location** | Forensic ledger persistence | ⚠️ Stores on `/tmp` (ephemeral) | 🔴 RED | Move to `/var/lib/mea/ledger.db` with mount point |
| **Database Migrations** | Schema versioning via `alembic` or raw SQL | ✅ 3 migrations present | 🟢 GREEN | Continue discipline; document ordering |
| **Connection String Validation** | SSL/TLS enforcement | ❓ Not documented | 🟡 YELLOW | Enforce `sslmode=require` in psycopg connection string |
| **Backup Strategy** | Automated backups documented | ❌ Missing | 🟡 YELLOW | Create backup runbook; test restore procedure |
| **Query Performance** | Slow query logging | ❓ Not documented | 🟡 YELLOW | Enable `log_min_duration_statement=1000` in PostgreSQL |
| **Transaction Rollback** | Ledger integrity on failure | ✅ Append-only design prevents corruption | 🟢 GREEN | Maintain current approach |

**Decision Rule:**

```
IF connection pooling missing OR SQLite on /tmp
  THEN risk = RED
  ACTION = "Fix before production; prevents connection exhaustion and data loss"
  
ELSE IF SSL/TLS not enforced OR backup strategy undocumented
  THEN risk = YELLOW
  ACTION = "Address before release"
  
ELSE IF migrations ordered AND append-only ledger verified
  THEN risk = GREEN
  ACTION = "Database readiness acceptable"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Blockers**: Missing connection pooling causes connection exhaustion under load
- **Action Items**:
  - [ ] Add `psycopg_pool.ConnectionPool` initialization in `shared/db.py`
  - [ ] Move forensic ledger from `/tmp` to `/var/lib/mea/` with persistence
  - [ ] Enforce `sslmode=require` in PostgreSQL connection string
  - [ ] Create backup/restore runbook
  - [ ] Document query performance baseline

---

### 6. OPERATIONAL HARDENING

**Scope:** Circuit breakers, graceful degradation, error handling, monitoring  
**Hit Policy:** FIRST

| Input | Criterion | Current State | Risk | Recommendation |
|-------|-----------|---------------|------|-----------------|
| **Circuit Breaker Pattern** | Redis/PostgreSQL resilience | ❌ Missing | 🟡 YELLOW | Add `pybreaker` library; fail-fast on Redis timeout |
| **Graceful Degradation** | Memory queue fallback masks Redis failures | ⚠️ Silent fallback | 🟡 YELLOW | Log fallback events; surface in healthz endpoint |
| **Custom Error Types** | Domain-specific exceptions | ❌ Missing | 🟡 YELLOW | Create `shared/exceptions.py` with: ConnectionError, SegmentError, ValidationError |
| **Error Handling in Worker** | Exponential backoff on empty polls | ✅ Implemented | 🟢 GREEN | Monitor backoff distribution |
| **Health Check Endpoint** | `/healthz` with dependency status | ⚠️ Basic; doesn't check Redis/DB | 🟡 YELLOW | Extend: check PostgreSQL, Redis, ledger disk space |
| **Rate Limiting** | Slowapi or equivalent | ❌ Missing | 🟡 YELLOW | Add rate limiting to prevent DoS |
| **Request Logging** | Structured logs with trace IDs | ❓ Not documented | 🟡 YELLOW | Add middleware: `logger.structlog` with request correlation IDs |

**Decision Rule:**

```
IF circuit breaker not implemented
  THEN risk = YELLOW
  ACTION = "Add before production; prevents cascading failures"
  
ELSE IF health checks incomplete OR custom errors missing
  THEN risk = YELLOW
  ACTION = "Improve before release; eases incident response"
  
ELSE IF exponential backoff verified AND error handling comprehensive
  THEN risk = GREEN
  ACTION = "Operational hardening acceptable"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Action Items**:
  - [ ] Add `pybreaker` circuit breaker for Redis
  - [ ] Extend `/healthz` to include dep status (DB, Redis, disk)
  - [ ] Create `shared/exceptions.py` with domain errors
  - [ ] Add request correlation IDs to logging
  - [ ] Add rate limiting middleware (slowapi)

---

### 7. TYPE SAFETY & CODE QUALITY

**Scope:** Type hints, mypy coverage, linting, code organization  
**Hit Policy:** COLLECT

| Input | Criterion | Current State | Risk | Recommendation |
|-------|-----------|---------------|------|-----------------|
| **Type Hints** | Coverage across codebase | ✅ Comprehensive | 🟢 GREEN | Maintain discipline; enforce in CI |
| **Mypy Strict Mode** | Type checking rigor | ⚠️ Standard mode only | 🟡 YELLOW | Consider migration to `--strict` for new code |
| **Linting** | ruff enforced in CI | ✅ Present | 🟢 GREEN | Maintain current rules |
| **Module Boundaries** | `control_plane/repository.py` likely oversized | ⚠️ Multiple responsibilities | 🟡 YELLOW | Refactor: split into models, queries, transactions |
| **Import Organization** | Predictable structure | ✅ Well-organized | 🟢 GREEN | Maintain |

**Decision Rule:**

```
IF type hints incomplete OR mypy coverage < 95%
  THEN risk = YELLOW
  ACTION = "Address incrementally; no blocker"
  
ELSE IF ruff linting passing AND imports organized
  THEN risk = GREEN
  ACTION = "Code quality acceptable"
```

**Output:**
- **Risk Level**: [RED/YELLOW/GREEN]
- **Action Items**:
  - [ ] Verify mypy passes with current strictness
  - [ ] Schedule refactor of `control_plane/repository.py` (non-blocking)

---

## Top-Level Decision Logic

### Decision Tree: "Is Codebase Ready for Production Deployment?"

```
START
  │
  ├─ Check DOCUMENTATION_QUALITY
  │  │
  │  ├─ RED? → BLOCKED
  │  │
  │  └─ YELLOW/GREEN? → Continue
  │
  ├─ Check SECURITY_AUDIT
  │  │
  │  ├─ RED? → BLOCKED (rotate credentials, fix leaks)
  │  │
  │  └─ YELLOW/GREEN? → Continue
  │
  ├─ Check DATABASE_READINESS
  │  │
  │  ├─ RED? → BLOCKED (connection pooling required)
  │  │
  │  └─ YELLOW/GREEN? → Continue
  │
  ├─ Check DEPENDENCY_MANAGEMENT
  │  │
  │  ├─ RED? → BLOCKED (lock file required)
  │  │
  │  └─ YELLOW/GREEN? → Continue
  │
  ├─ Check TEST_COVERAGE
  │  │
  │  ├─ RED? → BLOCKED (E2E tests required)
  │  │
  │  └─ YELLOW/GREEN? → Continue
  │
  ├─ Check OPERATIONAL_HARDENING
  │  │
  │  └─ YELLOW? → CAUTION (proceed with plan to address)
  │
  └─ OVERALL DECISION
     │
     ├─ RED items present? → "NOT_READY" (block merge/deploy)
     ├─ YELLOW items present? → "CAUTION" (proceed with sprint plan)
     └─ All GREEN? → "READY_FOR_PRODUCTION"
```

### Current State Assessment

| Domain | Status | Impact |
|--------|--------|--------|
| Documentation | 🔴 RED | Blocks onboarding; no DEPLOYMENT.md |
| Security | 🟡 YELLOW | Webhook secret not enforced; patch validation inverted |
| Database | 🔴 RED | No connection pooling; ledger on /tmp |
| Dependencies | 🔴 RED | Lock file missing; pyproject.toml inconsistent |
| Testing | 🔴 RED | No E2E tests for critical webhook pipeline |
| Operational Hardening | 🟡 YELLOW | No circuit breakers; health checks incomplete |
| Type Safety | 🟢 GREEN | Full mypy coverage; well-typed |

**OVERALL: 🔴 NOT READY FOR PRODUCTION DEPLOYMENT**

**Blockers to Address (before merge/deploy):**
1. Create README.md + DEPLOYMENT.md
2. Generate lock file; delete requirements.txt
3. Add connection pooling to PostgreSQL
4. Move forensic ledger from /tmp to persistent storage
5. Create E2E test suite

**To Address (before next release):**
1. Enforce webhook secret in production
2. Add circuit breaker for Redis
3. Upgrade patch validation to positive-model
4. Extend health check endpoint

---

## Manager Decision Rules & Policies

### Policy 1: Code Review Approval Decision

**When can a PR be merged?**

```
APPROVAL_ALLOWED = (
  documentation_quality >= YELLOW 
  AND security_audit >= YELLOW
  AND test_coverage >= YELLOW
  AND dependency_management >= YELLOW
  AND database_readiness >= YELLOW
  AND operational_hardening >= GREEN
)

IF APPROVAL_ALLOWED
  THEN status = "APPROVED_FOR_MERGE"
  ACTION = "Merge to main; schedule YELLOW items for next sprint"
  
ELSE
  THEN status = "REQUEST_CHANGES"
  ACTION = "Author must address RED items; rebase and re-request"
```

### Policy 2: Production Deployment Decision

**When can code deploy to production?**

```
DEPLOYMENT_ALLOWED = (
  all_domains >= GREEN 
  AND security_audit = GREEN
  AND test_coverage = GREEN
  AND database_readiness = GREEN
)

IF DEPLOYMENT_ALLOWED
  THEN status = "APPROVED_FOR_PRODUCTION"
  ACTION = "Deploy via release gate; monitor 24/7"
  
ELSE IF any_domain = RED
  THEN status = "DEPLOYMENT_BLOCKED"
  ACTION = "Fix blockers; create incident if affecting production"
  
ELSE IF any_domain = YELLOW
  THEN status = "DEPLOY_WITH_CAUTION"
  ACTION = "Deploy to staging; monitor closely; plan fixes for next sprint"
```

### Policy 3: Critical Security Findings

**Response to RED security findings:**

```
IF security_audit = RED
  THEN priority = "CRITICAL"
  
  IMMEDIATE_ACTIONS:
  1. Rotate all exposed credentials within 1 hour
  2. Scan git history for leaked secrets (truffleHog)
  3. Notify security team
  4. Create incident ticket
  5. Block all deployments until remediated
  6. Verify fix with security peer review
```

### Policy 4: Dependency Governance

**When introducing new dependencies:**

```
FOR each_new_dependency:
  1. Check license compatibility (use: licensecheck)
  2. Scan for known vulnerabilities (use: pip-audit)
  3. Verify dependency stability (check: GitHub stars, release frequency)
  4. Estimate dependency weight (size, download count)
  
  IF vulnerability_found = CRITICAL
    THEN reject_dependency; find alternative
    
  IF license_incompatible
    THEN reject_dependency; escalate to legal
    
  ELSE
    THEN approve; regenerate lock file; update CHANGELOG
```

### Policy 5: Testing Requirements by Module

| Module | Unit Tests | Integration Tests | E2E Tests | Coverage |
|--------|------------|-------------------|-----------|----------|
| `control_plane/` | ✅ Required | ✅ Required | ✅ Required (webhook → result) | 90%+ |
| `mea/policy_engine` | ✅ Required | ✅ Required | ❌ Not required | 95%+ |
| `worker/` | ✅ Required | ✅ Required | ✅ Required (job execution) | 85%+ |
| `shared/` | ✅ Required | ✅ If DB access | ❌ Not required | 90%+ |
| `ingest/iracing_stream` | ✅ Required | ⚠️ Mocked (Windows-only) | ❌ Not required | 80%+ |

### Policy 6: Performance SLOs

| Endpoint | Latency P99 | Throughput | Notes |
|----------|------------|-----------|-------|
| `/healthz` | <50ms | No limit | Must respond in <50ms |
| `/jobs/{id}` | <200ms | No limit | Query with caching |
| `/repos/fix-ci` | <2s | 100 req/sec | Async job queue; rate-limit |
| Webhook ingestion | <1s | 500 webhooks/sec | Fast validation; async processing |

---

## Escalation & Waiver Protocol

### When to Escalate RED Findings

**Escalation Path:**

```
Developer/Code Reviewer finds RED
  ↓
Create GitHub Issue (label: blocker, needs: <domain>)
  ↓
Notify engineering manager (@ralph-manager tag)
  ↓
Manager decides: Fix or waive?
  ↓
  ├─ FIX: Create sprint task; add to current/next iteration
  │
  └─ WAIVE: Document waiver (see Waiver Protocol below)
```

### Waiver Protocol

**Who can approve waivers?**
- 🟢 Manager (team lead or engineering director)
- ❌ Developer (cannot self-approve)
- ❌ Individual contributor (escalate to manager)

**Waiver criteria:**

```
WAIVER_ALLOWED IF:
  1. Risk is YELLOW (not RED)
  2. Documented business justification (deadline, roadmap, tech debt payoff)
  3. Signed off by manager + architect
  4. Tracked in GitHub Issue (tag: waived-risk)
  5. Remediation task created (label: debt, priority: medium)
  6. Timeline commitment (fix by date: YYYY-MM-DD)

WAIVER_BLOCKED IF:
  1. Risk is RED (security, data loss, architectural flaw)
  2. Affects production SLOs
  3. Introduces unmitigated risk to customers
```

**Waiver format:**

```markdown
## Waiver Request: [Domain] - [Brief Description]

**Risk Level:** YELLOW
**Duration:** [Sprint start] - [Expected fix date]

### Business Justification
[Why this waiver is necessary for business priorities]

### Mitigation Plan
[How we'll reduce risk during waiver period]

### Remediation Task
[Link to GitHub Issue tracking the fix]

**Approved by:** [Manager Name] on [Date]
**Architecture review:** [Architect Name] on [Date]
```

### When Risk Escalates from YELLOW to RED

```
YELLOW → RED if any of:
1. YELLOW item remains unaddressed for >2 sprints
2. Incident occurs caused by YELLOW gap
3. Multiple related YELLOW items form systemic risk
4. Security/data loss risk increases due to new findings

ACTION:
  ├─ Notify manager immediately
  ├─ Move to critical sprint item
  ├─ Consider partial deployment freeze
  └─ Dedicate engineer 100% to remediation
```

---

## Implementation Guidance

### For Code Reviewers: Review Checklist

**Before approving a PR, verify:**

1. **Documentation** (If changes affect public API or deployment):
   - [ ] README updated (if architecture changed)
   - [ ] Docstrings added to new functions
   - [ ] API endpoint docstring includes examples
   - [ ] CHANGELOG.md entry added

2. **Security** (Always verify):
   - [ ] No hardcoded secrets in code
   - [ ] Environment variables used for credentials
   - [ ] HMAC validation present if handling webhooks
   - [ ] SQL queries use parameterized queries (not f-strings)

3. **Testing** (If logic changed):
   - [ ] Unit tests added/updated
   - [ ] E2E tests added if critical path changed
   - [ ] `pytest -v --cov=<module>` shows coverage gain (not loss)
   - [ ] All tests pass locally and in CI

4. **Database** (If DB schema changed):
   - [ ] Migration file created (not inline SQL)
   - [ ] Rollback logic verified
   - [ ] No breaking schema changes without deprecation period

5. **Dependencies** (If new dependency added):
   - [ ] Lock file regenerated
   - [ ] `pip-audit` passes (no CVEs)
   - [ ] License check passes
   - [ ] Transitive deps checked for bloat

6. **Type Safety** (Always):
   - [ ] Mypy passes with no `type: ignore` comments (or justified)
   - [ ] Pydantic models used for API contracts
   - [ ] Return types explicitly annotated

**Risk Assessment:**
- After verifying all items, assign risk level: GREEN / YELLOW / RED
- Add comment: `Risk Assessment: [LEVEL] - [Brief summary]`
- If YELLOW/RED: mention in PR title or request changes

### For Engineering Managers: Release Decision Template

**Before approving a release, complete this checklist:**

```markdown
# Release Approval Checklist - v[VERSION]

## Risk Assessment

### Documentation
- [ ] README complete and current
- [ ] DEPLOYMENT.md reflects current setup
- [ ] CHANGELOG updated with all breaking changes
- [ ] API documentation current
- Status: [GREEN/YELLOW/RED]

### Security
- [ ] No secrets in code (truffleHog scan passed)
- [ ] Webhook secret configured in production
- [ ] Patch validation uses positive-model allowlist
- [ ] Dependencies scanned with pip-audit
- Status: [GREEN/YELLOW/RED]

### Testing
- [ ] Unit test coverage >= 85%
- [ ] E2E test suite passes (all critical paths)
- [ ] Load tests show acceptable perf degradation (<25% latency increase at 10x load)
- [ ] No known flaky tests
- Status: [GREEN/YELLOW/RED]

### Database
- [ ] Connection pooling configured (min=5, max=20)
- [ ] Migrations tested (forward + rollback)
- [ ] Backup strategy verified and tested
- [ ] Schema changes documented
- Status: [GREEN/YELLOW/RED]

### Operational Hardiness
- [ ] Circuit breaker configured for Redis/PostgreSQL
- [ ] Health check endpoint responds in <50ms
- [ ] Rate limiting active on `/repos/fix-ci`
- [ ] Monitoring dashboards created for new metrics
- [ ] Runbooks created for known failure modes
- Status: [GREEN/YELLOW/RED]

## Overall Decision

- [ ] All domains are GREEN or YELLOW (no RED blockers)
- [ ] YELLOW items have documented remediation plan
- [ ] Deployment window scheduled with on-call engineer
- [ ] Rollback plan documented and tested

**Approval:** [Manager name] on [Date]
**Architecture Sign-Off:** [Architect name] on [Date]
```

### For Architects: Architecture Review Process

**Quarterly Architecture Review (driven by DMN):**

1. **Run DMN Assessment** on current main branch
2. **Generate Report**: Document each domain's status (RED/YELLOW/GREEN)
3. **Escalate RED items**: Create critical tasks
4. **Plan YELLOW items**: Schedule for roadmap
5. **Track GREEN items**: Monitor for drift
6. **Communicate to team**: Share findings in retrospective

**Example output:**

```
# Q2 2026 Architecture Review

Assessment Date: 2026-04-04
Reviewed Branch: main (commit abc123)

## Current State

| Domain | Status | Trend | Action |
|--------|--------|-------|--------|
| Documentation | 🔴 RED | ↑ Improving | 2 sprints |
| Dependencies | 🟢 GREEN | ↔️ Stable | Monitor |
| Security | 🟡 YELLOW | ↑ Improving | 1 sprint |
| Testing | 🟡 YELLOW | ↑ Improving | 2 sprints |
| Database | 🟢 GREEN | ↑ Improving | Monitor |
| Operational Hardening | 🟡 YELLOW | ↔️ Stable | 1 sprint |

## Metrics
- Type Coverage: 98%
- Test Coverage: 78%
- Production Incidents (last 90 days): 1 (Redis fallback)
- MTTR: 15 minutes (average)

## Priorities for Next Quarter
1. Complete E2E test suite (blocks deployment)
2. Implement circuit breaker (reduces cascading failures)
3. Extend health check endpoint (improves observability)
```

### Integrating DMN into CI/CD Pipeline

**GitHub Actions Workflow:**

```yaml
name: DMN Review Gate

on: [pull_request, push]

jobs:
  dmn-assessment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check Documentation
        run: |
          if [[ ! -f "README.md" ]]; then
            echo "ERROR: README.md missing (RED: DOCUMENTATION)"
            exit 1
          fi
          
      - name: Check Dependency Lock File
        run: |
          if [[ ! -f "requirements.lock" ]] && [[ ! -f "uv.lock" ]]; then
            echo "ERROR: No lock file found (RED: DEPENDENCIES)"
            exit 1
          fi
          
      - name: Security Scan
        run: |
          pip-audit || echo "⚠️ YELLOW: Audit findings"
          
      - name: Test Coverage
        run: |
          pytest --cov=. --cov-fail-under=80 || exit 1
          
      - name: Type Checking
        run: |
          mypy . --ignore-missing-imports || exit 1
          
      - name: Generate DMN Report
        run: |
          python scripts/dmn_assessment.py > .github/dmn-report.md
          
      - name: Comment PR with DMN Result
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.github/dmn-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

---

## Summary: Manager Decision Framework

### Quick Reference

| Decision | Question | When | Who | Output |
|----------|----------|------|-----|--------|
| **Code Review** | Should we merge this PR? | On PR creation | Reviewer + Manager | ✅ Merge / ❌ Request Changes |
| **Deployment** | Should we ship to production? | Before release | Manager + Architect | ✅ Deploy / ⏸️ Hold / ❌ Block |
| **Critical Fix** | Is this a security blocker? | On security finding | Manager + SecOps | 🔴 Critical / 🟡 High / 🟢 Medium |
| **Architecture** | What's our technical health? | Quarterly | Architect + Manager | 📊 Report + Priorities |

### The DMN in One Sentence

> **A PR is mergeable if all critical domains achieve YELLOW or better; a release is deployable only if all domains achieve GREEN; violations follow a documented escalation path with manager approval required for waivers.**

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-04  
**Maintained by:** Engineering Manager (Ralph Wiggum)  
**Review Frequency:** Quarterly (or after critical incidents)
