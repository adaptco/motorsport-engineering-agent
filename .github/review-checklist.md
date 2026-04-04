# Code Review Checklist - Based on DMN Decision Framework

**Purpose:** Practical checklist for code reviewers to apply the DMN decision model during PR reviews  
**Level:** All code reviews (use abbreviated version for minor changes, full version for major features)  
**How to Use:** Copy checklist into PR comment; ✅ items as verified

---

## Quick Assessment (All Reviews)

> Start here for every PR review

- [ ] **PR title descriptive?** (summarizes change, not just "fix bug")
- [ ] **Linked to GitHub issue?** (include issue #, PRD, or epic)
- [ ] **Commit history clear?** (each commit has meaningful message with `Co-authored-by` trailer)
- [ ] **CI passing?** (no failed checks; all workflows green)

---

## Domain Checklists

### 🟡 DOCUMENTATION (If changes affect API, deployment, or user-facing features)

**Required for:**
- API endpoint changes
- Configuration changes
- Deployment procedure changes
- User-facing feature changes
- Database schema changes
- Security policy changes

**Checklist:**

- [ ] **README.md** - If architecture/setup changed, README updated or verified current
- [ ] **API Docstrings** - New FastAPI endpoints include docstrings with:
  - Description of purpose
  - Request/response examples (if non-obvious)
  - Error cases (`raises` section)
- [ ] **CHANGELOG.md** - Entry added with version, date, description of change
- [ ] **Breaking Changes** - If applicable, documented and communicated:
  - What changed
  - Migration path for users
  - Deprecation timeline (if phased)
- [ ] **Deployment Guide** - If new env vars or config required, DEPLOYMENT.md updated
- [ ] **Database Schema** - If migrations included, migration file describes what changed and why

**Risk If Missing:**
- 🟡 YELLOW if documentation incomplete (e.g., docstring exists but no examples)
- 🔴 RED if critical API or deployment changes undocumented

**Decision:** 
- ✅ **Approve** if documentation meets requirements or changes don't require docs
- ❌ **Request Changes** if RED items missing; mark as YELLOW if YELLOW items need follow-up

---

### 🔐 SECURITY (Always verify for every change)

**Checklist:**

- [ ] **No Hardcoded Secrets** - Run: `grep -r "password\|api_key\|secret" --include="*.py" | grep -v test`
  - ❌ Fail if secrets found
  - ✅ Pass if all secrets use environment variables or `.env` file
- [ ] **Environment Variables** - Sensitive data uses `os.environ` or `Pydantic.SettingsConfigDict`
  - [ ] `.env.example` includes all new env var names (without values)
- [ ] **Webhook/API Auth** - If handling webhooks:
  - [ ] HMAC-SHA256 validation present
  - [ ] Secret required (not optional)
  - [ ] Invalid signatures rejected with 401/403
- [ ] **SQL Injection** - If DB queries added:
  - [ ] Using parameterized queries (psycopg `%s` placeholders)
  - ❌ NOT f-strings or string concatenation
- [ ] **Cryptography** - If generating/validating tokens:
  - [ ] Using `PyJWT` or equivalent (not custom crypto)
  - [ ] Signing algorithm specified (e.g., `algorithm="HS256"`)
  - [ ] Secret key comes from environment
- [ ] **File Operations** - If reading/writing files:
  - [ ] Path validation (no path traversal via `..`)
  - [ ] File permissions explicitly set (not relying on defaults)
  - [ ] Temporary files use `tempfile` module (not `/tmp` directly)
- [ ] **Dependencies** - If new dependencies added:
  - [ ] `pip-audit` passes (no CVEs in new dependencies)
  - [ ] License compatible with project (check in PR description)
  - [ ] Transitive dependencies reasonable (not bloat)

**Risk If Missing:**
- 🔴 RED if: Secrets in code, no webhook validation, SQL injection possible, custom crypto
- 🟡 YELLOW if: File operations lack validation, new dependencies not audited

**Decision:**
- ✅ **Approve** if no security concerns or RED items addressed
- ❌ **Request Changes** if RED items; mark as YELLOW if YELLOW items

---

### 🧪 TESTING (If logic changed, always verify)

**Checklist:**

- [ ] **Unit Tests** - New functions have unit tests:
  - [ ] Positive cases (happy path)
  - [ ] Negative cases (error paths)
  - [ ] Edge cases (empty, null, max values)
  - [ ] Mock external dependencies (DB, Redis, API calls)
  - ✅ Pass locally: `pytest -v tests/test_<module>.py`

- [ ] **Integration Tests** - If component touches DB or external service:
  - [ ] Test with actual DB (or test database)
  - [ ] Test Redis fallback (if applicable)
  - [ ] Setup/teardown cleans up test data
  - ✅ Pass locally: `pytest -v tests/integration/`

- [ ] **E2E Tests** - If critical user workflow changed:
  - [ ] End-to-end flow tested (e.g., webhook → job queue → result)
  - [ ] Fixtures include: test webhook payload, expected outputs
  - [ ] Run: `pytest -v tests/e2e/`

- [ ] **Coverage** - Run: `pytest --cov=<module> --cov-report=html`
  - [ ] Coverage >= 85% for modified module (not decrease)
  - [ ] New branches covered (if/else, try/except)
  - Check: `htmlcov/index.html` for untested lines

- [ ] **Mock Strategy** - If mocking external services:
  - [ ] Using `pytest-mock` or `responses` (not `unittest.mock` directly)
  - [ ] Mocks configured in fixtures (`conftest.py`)
  - [ ] Mock behavior documents expected service contract
  - [ ] No brittle mocks that break on minor service changes

- [ ] **Flaky Tests** - If test times are non-deterministic:
  - [ ] No `time.sleep()` calls (use `freezegun` instead)
  - [ ] No real-time dependencies (use fixed clock)
  - [ ] No random seeds without explicit set (use `random.seed(42)`)

**Risk If Missing:**
- 🔴 RED if: Critical path has no E2E tests, coverage decreases, tests fail in CI
- 🟡 YELLOW if: Coverage < 85%, no integration tests for DB changes, missing edge cases

**Decision:**
- ✅ **Approve** if tests pass, coverage maintained/improved
- 🟡 **Request Changes (YELLOW)** if coverage weak but logic sound; author can improve in follow-up
- ❌ **Request Changes** if RED items or tests fail

---

### 📦 DEPENDENCIES (If new dependencies added)

**Checklist:**

- [ ] **Lock File** - After dependencies changed:
  - [ ] `uv.lock` or equivalent regenerated
  - ✅ Commit lock file in same PR (not separate commit)
  - Run: `uv pip compile > requirements.lock` (or equivalent)

- [ ] **Requirements Consistency** - Verify single source of truth:
  - ✅ `pyproject.toml` is primary source
  - ❌ `requirements.txt` should not exist (delete if present)
  - [ ] Lock file matches `pyproject.toml` (run: `uv pip compile --verify`)

- [ ] **Security Audit** - For each new dependency:
  - [ ] Run: `pip-audit --desc | grep -i "<new-package>"`
  - ❌ Fail if CRITICAL or HIGH vulnerabilities found
  - ✅ Known LOW/MEDIUM OK if mitigated in code

- [ ] **License Check** - Verify compatibility:
  - [ ] Run: `licensecheck --zero MIT Apache-2.0 GPL-3.0` (adjust for your policy)
  - ❌ Fail if incompatible license (e.g., GPL vs proprietary)
  - [ ] If unsure, escalate to manager/legal

- [ ] **Version Pinning** - Check dependency specification:
  - ✅ Pinned versions: `package==1.2.3` (not `package>=1.2.3`)
  - ✅ Transitive deps locked via lock file
  - ❌ Not overly restrictive (allow minor upgrades)

- [ ] **Transitive Dependencies** - Check bloat:
  - [ ] Run: `pip install <new-package> && pip tree | wc -l` (total dep count)
  - ⚠️ Alert if transitive deps > 10 (likely bloat)
  - [ ] Verify no conflicting transitive dependencies

- [ ] **CI Tool Versions** - If changing CI tools (ruff, mypy, etc.):
  - [ ] Versions explicitly pinned in `.github/workflows/ci.yml`
  - [ ] Not relying on floating tags (e.g., `ruff@latest`)
  - [ ] Pin format: `- run: pip install ruff==0.X.Y mypy==1.X.Y`

**Risk If Missing:**
- 🔴 RED if: No lock file, unresolved CVEs, license conflict, requirements.txt stale
- 🟡 YELLOW if: New transitive deps not audited, CI versions not pinned

**Decision:**
- ✅ **Approve** if lock file present, audit passed, no conflicts
- ❌ **Request Changes** if RED items; YELLOW if author needs to audit

---

### 💾 DATABASE (If schema or queries changed)

**Checklist:**

- [ ] **Migrations** - New schema changes include migration file:
  - [ ] File named `db/migrations/<timestamp>_<description>.sql` or Alembic format
  - [ ] Migration includes both UP (apply) and DOWN (rollback)
  - [ ] Migration has been tested locally: `psql < migration.sql`
  - ✅ No breaking changes without deprecation period

- [ ] **Connection Pooling** - Queries use connection pool, not direct connections:
  - [ ] Code uses `psycopg_pool.ConnectionPool` or equivalent
  - ✅ Not creating new connection per query
  - [ ] Pool size documented (min=5, max=20 recommended)

- [ ] **SQL Injection** - Verify query safety:
  - [ ] Using parameterized queries: `cur.execute("SELECT * FROM users WHERE id = %s", [user_id])`
  - ❌ NOT: `f"SELECT * FROM users WHERE id = {user_id}"`
  - [ ] Using Pydantic models for input validation

- [ ] **Transactions** - Multi-step operations:
  - [ ] Wrapped in transaction: `BEGIN ... COMMIT` or context manager
  - [ ] Error handling includes `ROLLBACK` on exception
  - [ ] Audit trail updated atomically with schema changes

- [ ] **Indexes** - Performance optimization:
  - [ ] Added for frequently queried columns (WHERE, JOIN, ORDER BY)
  - [ ] Migration includes index creation with clear naming
  - [ ] Analyzed impact with `EXPLAIN ANALYZE`

- [ ] **Constraints** - Data integrity:
  - [ ] Foreign keys defined for relationships
  - [ ] Unique constraints prevent duplicates (if applicable)
  - [ ] NOT NULL constraints on required fields
  - [ ] Check constraints for domain validity (e.g., `status IN (...)`)

- [ ] **Backup/Restore** - If production-critical schema:
  - [ ] Backup procedure documented in DEPLOYMENT.md
  - [ ] Restore procedure tested
  - [ ] Retention policy defined (e.g., 30 days backups)

**Risk If Missing:**
- 🔴 RED if: No migration file, SQL injection possible, no rollback plan, breaking schema change
- 🟡 YELLOW if: No indexes on new columns, constraints missing, backup plan undocumented

**Decision:**
- ✅ **Approve** if migration safe, parameterized queries, indexes added
- ❌ **Request Changes** if RED items; mark YELLOW if schema performance concerns

---

### ⚙️ OPERATIONAL HARDENING (For production-facing changes)

**Checklist:**

- [ ] **Error Handling** - All code paths have error handling:
  - [ ] Try/except blocks for external service calls (Redis, DB, HTTP)
  - [ ] Specific exception types caught (not bare `except:`)
  - [ ] Error logged with context (not just silently ignored)
  - [ ] User-facing error message (not internal exception)

- [ ] **Circuit Breaker** - For external service failures:
  - [ ] If calling Redis/PostgreSQL: uses `pybreaker` or equivalent
  - [ ] Fails fast (doesn't retry endlessly)
  - [ ] Health check recovers circuit (via `/healthz`)
  - ✅ Graceful degradation (fallback if available)

- [ ] **Logging** - New operations are observable:
  - [ ] Request IDs propagated (correlation tracking)
  - [ ] Structured logging with context (use `logger.structlog` or `loguru`)
  - [ ] Appropriate log levels (DEBUG/INFO/WARNING/ERROR)
  - [ ] Sensitive data not logged (no secrets, API keys, PII)
  - Run locally: Verify logs readable and informative

- [ ] **Health Checks** - `/healthz` endpoint updated if needed:
  - [ ] Includes new external dependency status
  - [ ] Responds in <50ms
  - [ ] Returns: `{"status": "healthy", "checks": {...}}`

- [ ] **Rate Limiting** - For public endpoints:
  - [ ] `/repos/fix-ci` has rate limit: 100 req/sec per IP (configurable)
  - [ ] Using `slowapi` or equivalent middleware
  - [ ] Returns 429 Too Many Requests when exceeded
  - [ ] Admin bypass for internal calls (if needed)

- [ ] **Monitoring** - New metrics added to observability:
  - [ ] New endpoints have latency metrics (P50, P95, P99)
  - [ ] New jobs have success/failure counts
  - [ ] New external calls have timeout metrics
  - [ ] Metrics exposed via `/metrics` (Prometheus format)

**Risk If Missing:**
- 🟡 YELLOW if: No circuit breaker, minimal logging, no rate limiting, health checks incomplete

**Decision:**
- ✅ **Approve** if error handling comprehensive, observability good
- 🟡 **Mark YELLOW** if hardening incomplete but not blocking; plan improvements

---

### 🔤 TYPE SAFETY & CODE QUALITY (All reviews)

**Checklist:**

- [ ] **Type Hints** - All new functions have return type annotations:
  - ✅ `def get_user(user_id: int) -> User:` (good)
  - ❌ `def get_user(user_id):` (missing type)
  - [ ] Complex types use `from typing import List, Optional, Union` or Python 3.10+ syntax
  - [ ] No `type: ignore` comments without justification

- [ ] **Mypy Type Checking** - Run: `mypy . --ignore-missing-imports`
  - ✅ All errors fixed (not ignored)
  - ✅ If `type: ignore` used, has explanatory comment: `# type: ignore[error-code]`

- [ ] **Pydantic Models** - API contracts use Pydantic:
  - ✅ Request bodies: `@app.post("/jobs", body: JobRequest)`
  - ✅ Response models: `-> JobResponse`
  - [ ] Validation rules documented (length, pattern, constraints)

- [ ] **Linting** - Run: `ruff check .`
  - ✅ No style violations
  - ✅ Imports organized (standard lib, third-party, local)
  - ✅ Line length < 88 characters (ruff default)

- [ ] **Code Organization** - Module responsibilities clear:
  - [ ] No files > 500 lines (too large, needs refactoring)
  - [ ] Imports at top of file (no circular imports)
  - [ ] Constants in CONSTANTS or config module (not magic numbers)
  - [ ] Classes/functions have single responsibility

- [ ] **Naming** - Variables/functions have clear names:
  - ✅ `user_name`, `get_user()`, `MAX_RETRIES` (clear)
  - ❌ `u`, `gU()`, `mr` (unclear)
  - [ ] No misleading names (`is_valid` that returns list, etc.)

**Risk If Missing:**
- 🟢 GREEN if: Type hints complete, mypy passes, linting OK (code quality acceptable)
- 🟡 YELLOW if: Minor type safety gaps, 1-2 `type: ignore` comments

**Decision:**
- ✅ **Approve** if type safety strong, linting passes, no quality concerns
- 🟡 **Mark YELLOW** if minor gaps but logic sound; plan improvements

---

## Risk Assessment Template

After reviewing all domains, add this comment to the PR:

```markdown
## 📋 DMN Risk Assessment

### Summary
[Choose one]
- ✅ **GREEN**: All domains acceptable; approve for merge
- 🟡 **YELLOW**: [List YELLOW items]; approve with note to track improvements
- 🔴 **RED**: [List RED items]; request changes before merge

### Domain Status
- Documentation: [GREEN/YELLOW/RED]
- Security: [GREEN/YELLOW/RED]
- Testing: [GREEN/YELLOW/RED]
- Dependencies: [GREEN/YELLOW/RED]
- Database: [GREEN/YELLOW/RED]
- Operational Hardening: [GREEN/YELLOW/RED]
- Type Safety: [GREEN/YELLOW/RED]

### Action Items
- [Required changes if RED]
- [Suggested improvements if YELLOW]

### Reviewer
@[reviewer-name]

### Decision
[ ] Approve for merge
[ ] Request changes
```

---

## Abbreviation: Quick Review (Minor Changes)

**For small bug fixes, documentation updates, or non-critical changes:**

- [ ] CI passes (all workflows green)
- [ ] No security issues (no hardcoded secrets)
- [ ] Tests pass (if logic changed)
- [ ] Commit message clear and includes co-author trailer
- [ ] No breaking changes to public APIs

---

## Common Patterns to Watch For

| Pattern | Risk | Action |
|---------|------|--------|
| `import *` | 🟡 YELLOW | Request explicit imports |
| `except:` bare except | 🟡 YELLOW | Request specific exception types |
| `time.sleep()` in tests | 🟡 YELLOW | Request use of `freezegun` or mocking |
| `TODO` comments | 🟢 GREEN | Note; no action required (but track) |
| `print()` debugging | 🟡 YELLOW | Request use of `logger` instead |
| No error handling for API call | 🔴 RED | Request changes before merge |
| Hardcoded IP/domain | 🔴 RED | Request use of environment variable |
| `eval()` or `exec()` | 🔴 RED | Reject; use safer alternatives |

---

## Integration with GitHub PR Review

**How to use this checklist in GitHub:**

1. **Copy this template** into your PR review comment (can link to raw: `.github/review-checklist.md`)
2. **✅ Checkbox items** as you verify them
3. **Add risk assessment** at end of review
4. **Request changes** with specific requests (link to section above)
5. **Approve** once all required items checked

**Example PR comment:**

```markdown
Thanks for the PR! I've completed the review below.

## Documentation
- ✅ API docstring added with example
- ✅ CHANGELOG.md updated
- ✅ No breaking changes

## Security
- ✅ No hardcoded secrets
- ✅ Environment variables used for credentials
- ✅ SQL parameterized (no injection)

[... other domains ...]

## Risk Assessment
✅ **GREEN** - All domains acceptable; approve for merge

I'll merge this once CI passes. Great work!
```

---

## Notes for First-Time Reviewers

- **Start with the Quick Assessment** (top of this checklist)
- **Select applicable domain checklists** based on PR scope (not all domains for every PR)
- **Document your reasoning** in PR comments (helps author and future readers)
- **Ask questions** if unclear; better to clarify than guess
- **Be respectful** and assume good intent (framing suggestions positively)
- **Link to resources** when requesting changes (e.g., "See DEPLOYMENT.md for env vars")

---

## For Code Review Automation

If implementing automated checks, map this checklist to:

```yaml
# Example GitHub Actions workflow
checks:
  - name: documentation
    required: true if (api_changed OR deployment_changed)
    validation: [README updated, docstring present, CHANGELOG entry]
    
  - name: security
    required: true  # always
    validation: [no secrets, parameterized SQL, audit passed]
    
  - name: testing
    required: true if (logic_changed)
    validation: [coverage >= 85%, E2E if critical path]
    
  - name: dependencies
    required: true if (new_deps)
    validation: [lock file updated, audit passed, license OK]
    
  - name: database
    required: true if (schema_changed)
    validation: [migration file present, rollback tested]
    
  - name: type_safety
    required: true  # always
    validation: [mypy passes, no type ignore abuse]
```

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-04-04  
**Reference:** `.github/dmn-manager-decisions.md`
