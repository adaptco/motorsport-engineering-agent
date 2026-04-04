# DMN Implementation Guide - Quick Start

**Completed:** April 4, 2026  
**Status:** ✅ READY FOR TEAM REVIEW  
**Maintained By:** Engineering Manager (Ralph Wiggum)

---

## What Was Created

### Primary Documents

1. **`.github/dmn-manager-decisions.md`** (879 lines, 32.2 KB)
   - Comprehensive Decision Model & Notation
   - 7 decision domains with tables and logic
   - Risk framework (RED/YELLOW/GREEN)
   - Manager decision rules and policies
   - Escalation and waiver protocols
   - Implementation guidance for all roles

2. **`.github/review-checklist.md`** (527 lines, 18.4 KB)
   - Practical code review checklist
   - Domain-specific verification items
   - Risk assessment template
   - Quick reference for common patterns
   - Integration examples for GitHub automation

---

## Current Assessment: NOT READY FOR PRODUCTION

### 🔴 RED Blockers (Must Fix Before Merge/Deploy)

| Domain | Issue | Action | Timeline |
|--------|-------|--------|----------|
| **Documentation** | No README or DEPLOYMENT.md | Create both with diagrams | This sprint |
| **Dependencies** | No lock file, inconsistent pyproject.toml | Delete requirements.txt, generate lock | This sprint |
| **Database** | No connection pooling, ledger on /tmp | Add pooling, move ledger | This sprint |
| **Testing** | No E2E tests for webhook pipeline | Create E2E suite | Next sprint |

### 🟡 YELLOW Cautions (Address Next Sprint)

| Domain | Issue | Action | Timeline |
|--------|-------|--------|----------|
| **Security** | Webhook secret not enforced | Make required in production | Next sprint |
| **Security** | Patch validation inverted (negative model) | Switch to positive-model | Sprint +2 |
| **Operations** | No circuit breaker for Redis/PostgreSQL | Add pybreaker library | Next sprint |
| **Operations** | Incomplete health checks | Extend /healthz endpoint | Next sprint |

### 🟢 GREEN (Maintain Current)

| Domain | Status | Notes |
|--------|--------|-------|
| **Type Safety** | ✅ Comprehensive | 98% mypy coverage, maintain discipline |
| **Code Quality** | ✅ Strong | ruff enforced, imports organized |
| **Architecture** | ✅ Well-structured | Clear module boundaries |

---

## How to Use This DMN

### For Code Reviewers

**Every PR Review:**

1. Copy the checklist from `.github/review-checklist.md` into your PR comment
2. Go through each applicable domain (not all domains for every PR)
3. ✅ Check off items as you verify them
4. Complete the "Risk Assessment" section at bottom
5. Approve or request changes based on risk level

**Example:**
```markdown
## 📋 DMN Risk Assessment

### Domain Status
- Documentation: ✅ GREEN (docstring added)
- Security: ✅ GREEN (no secrets, parameterized SQL)
- Testing: ✅ GREEN (coverage improved to 86%)
- Dependencies: 🟡 YELLOW (new dep not yet audited)

Risk: 🟡 YELLOW - Approve with note to audit dependency before release
```

### For Managers

**Code Review Approvals:**
- ✅ Approve if no RED items (YELLOW OK with remediation plan)
- ❌ Request changes if RED items present
- 🟡 Approve YELLOW items with sprint assignment

**Release Approvals:**
- Use the release checklist from dmn-manager-decisions.md
- Require: All domains GREEN or YELLOW with acceptance
- Document: Waivers with business justification

**Quarterly Assessments:**
- Run DMN on main branch
- Generate status report
- Create critical sprint tasks
- Share findings in retrospective

### For Architects

**Waiver Authority:**
- Can approve/reject waivers for YELLOW items
- Must sign off on all RED→production decisions
- Required for security escalations

**Design Reviews:**
- Reference decision tables for thresholds
- Use to identify architectural gaps early

### For CI/CD

**Automate Key Gates:**

```yaml
# Example GitHub Actions
- Check if README.md exists (doc change)
- Verify no secrets with truffleHog
- Require coverage >= 85%
- Fail if lock file missing (dep added)
- Run mypy, ruff, pytest

# Comment PR with DMN status
```

---

## Implementation Roadmap

### This Sprint (IMMEDIATE)

- [ ] **README.md** - Create with architecture diagram, quick-start, Docker setup
- [ ] **DEPLOYMENT.md** - Production checklist, env vars, scaling guide
- [ ] **Lock File** - Run `uv pip compile`, commit to repo
- [ ] **Database Pooling** - Add `psycopg_pool` to `shared/db.py`

**Why:** Unblock deployment reviews, enable onboarding, resolve dependency conflicts

### Next Sprint (Sprint +1)

- [ ] **E2E Tests** - Create fixtures for webhook → job → result flow
- [ ] **Ledger Move** - Migrate from /tmp to /var/lib/mea/
- [ ] **Webhook Security** - Enforce `GITHUB_WEBHOOK_SECRET` in production
- [ ] **Circuit Breaker** - Add `pybreaker` for Redis/PostgreSQL
- [ ] **Health Checks** - Extend `/healthz` to test DB/Redis connectivity

**Why:** Improve reliability, enhance security, reduce cascading failures

### Sprint +2 (Polish)

- [ ] **Patch Validation** - Upgrade to positive-model (AST allowlist)
- [ ] **Dependency Audit** - Add `pip-audit` to CI
- [ ] **Custom Errors** - Create `shared/exceptions.py` domain hierarchy
- [ ] **Request Logging** - Add correlation IDs and structured logging

**Why:** Reduce incident response time, prevent vulnerability drift, improve debuggability

### Ongoing

- [ ] **Quarterly Reviews** - DMN assessment + report
- [ ] **PR Checklist** - Apply on every merge
- [ ] **Waiver Tracking** - Monitor YELLOW items, escalate if not addressed
- [ ] **Metrics** - Track coverage, security, MTTR trends

---

## Key Decision Rules

### Rule 1: Can This PR Be Merged?

```
MERGEABLE IF:
  documentation_quality >= YELLOW
  AND security_audit >= YELLOW
  AND test_coverage >= YELLOW
  AND dependency_management >= YELLOW
  AND database_readiness >= YELLOW
  AND operational_hardening >= YELLOW
  AND type_safety >= GREEN

ACTION IF MERGEABLE:
  ✅ Approve → Merge to main
  Plan next sprint work for YELLOW items
  
ACTION IF NOT MERGEABLE:
  ❌ Request changes
  Point to specific RED items
  Link to remediation plan if exists
```

### Rule 2: Can This Release Deploy to Production?

```
DEPLOYABLE IF:
  all_domains >= GREEN
  OR (all domains >= YELLOW AND manager acceptance signed)

ACTION IF DEPLOYABLE:
  ✅ Deploy → Full deployment procedure
  Activate monitoring + on-call
  Document any YELLOW items in runbook
  
ACTION IF NOT DEPLOYABLE:
  ⏸️ Hold → Fix RED items
  Create incident if affecting production
  Escalate to manager + architect
```

### Rule 3: Security Finding Response

```
IF security_issue = RED:
  PRIORITY = CRITICAL
  
  IMMEDIATE (< 1 hour):
  1. Rotate all exposed credentials
  2. Scan git history for secrets (truffleHog)
  3. Notify security team
  4. Block deployments
  5. Create incident ticket
  
  NEXT (< 24 hours):
  1. Root cause analysis
  2. Implement fix
  3. Security peer review
  4. Resume deployments

ESCALATE TO:
  - CISO (if customer data affected)
  - Legal (if compliance violation)
  - Management (executive notification)
```

---

## Common Review Scenarios

### Scenario 1: Small Bug Fix

```
PR: Fix off-by-one error in policy engine

✅ QUICK ASSESSMENT:
□ Title clear (yes: "Fix off-by-one in policy priority")
□ Linked to issue (yes: closes #1234)
□ CI passing (yes: all green)
□ Commits meaningful (yes: single commit)

🧪 TESTING:
□ Unit test added (yes, 3 test cases)
□ Coverage maintained (yes, 98% → 98%)

🔤 TYPE SAFETY:
□ Mypy passes (yes)
□ No type: ignore comments (yes)

✅ DECISION: GREEN - Approve

Risk Assessment: All green, maintainability preserved.
```

### Scenario 2: New API Endpoint

```
PR: Add /jobs/{id}/logs endpoint

📋 DOCUMENTATION:
□ FastAPI docstring (yes, with examples)
□ CHANGELOG.md (no, request addition)
□ README API section (yes)

🧪 TESTING:
□ Unit tests (yes, 5 test cases)
□ E2E test (no, request E2E for critical path)
□ Coverage >= 85% (yes, 87%)

🔐 SECURITY:
□ Proper auth check (yes, bearer token)
□ No SQL injection (yes, parameterized)
□ Rate limiting (yes, 100 req/sec)

🔤 TYPE SAFETY:
□ Mypy passes (yes)
□ Return type annotated (yes)

🟡 DECISION: YELLOW - Approve with follow-up

Risk: Missing CHANGELOG entry and E2E test
Action: Author adds in follow-up PR, merged without blocking

Risk Assessment: Core logic sound, can address polish items soon.
```

### Scenario 3: New Dependency Addition

```
PR: Add FastAPI-CORS for cross-origin support

📦 DEPENDENCIES:
□ Lock file updated (yes, regenerated)
□ pyproject.toml updated (yes)
□ pip-audit passed (no, 1 MEDIUM CVE found)
□ License OK (yes, Apache 2.0)

🔓 SECURITY:
□ CVE assessed (MEDIUM in transitive dep)
□ Mitigation plan (not applicable, low-risk endpoint)

🔴 DECISION: YELLOW - Approve with audit note

Risk: MEDIUM CVE in transitive dependency
Action: Request author acknowledge in PR comment, create tracking issue
Timeline: Schedule for next sprint if update available

Risk Assessment: Non-critical endpoint, update available Q3
```

### Scenario 4: Database Schema Change

```
PR: Add connection pooling config to PostgreSQL init

💾 DATABASE:
□ Migration file (yes, 001_add_pool_config.sql)
□ Rollback tested (yes, local testing)
□ Indexes added (yes, on foreign keys)
□ Connection pooling (yes, min=5, max=20)

📋 DOCUMENTATION:
□ DEPLOYMENT.md updated (no, request update)
□ Migration commented (yes, explains why)

🧪 TESTING:
□ Integration tests (yes, with real DB)
□ Load test (yes, simulated 10x traffic)
□ Coverage (yes, 86%)

✅ DECISION: YELLOW - Approve pending doc update

Risk: Missing deployment configuration docs
Action: Author updates DEPLOYMENT.md before merge

Risk Assessment: Config safe, critical for production, doc gap must be closed.
```

---

## Metrics Dashboard (Track Over Time)

### Health Checks

```
✅ Type Safety: 98% mypy pass (target: 100%)
✅ Test Coverage: 78% → target 85%+ 
⚠️  Security: 0 CRITICAL, 1 YELLOW (webhook), 1 YELLOW (patch)
⚠️  Documentation: 40% complete (target: 100% public APIs)
✅ Code Quality: ruff 0 violations
✅ Incidents (90d): 1 Redis fallback (MTTR: 15 min)
```

### Monthly Review

- Coverage trend: Increasing/flat/decreasing?
- Security findings: New/resolved this month?
- MTTR: Improving/stable/degrading?
- YELLOW items: Being addressed on schedule?

---

## FAQ

**Q: Can we waive a RED item?**  
A: No. RED items block deployment. Fix or escalate to architecture committee.

**Q: How long can YELLOW items stay?**  
A: Max 2 sprints. If not addressed, escalate to RED.

**Q: Who can approve waivers?**  
A: Manager + Architect (both required). No self-approval.

**Q: What if manager and architect disagree?**  
A: Escalate to engineering director. Decision required within 24 hours.

**Q: Can we merge with failing tests?**  
A: No. Tests must pass in CI. Manual exceptions are RED findings.

**Q: How do we handle false positives (e.g., security scan)?**  
A: Document in PR comment, get security team sign-off, create follow-up issue to improve scanner.

---

## Support & Questions

For questions about:
- **Decision logic:** Review the decision tables in `dmn-manager-decisions.md`
- **Practical application:** See examples in `review-checklist.md`
- **Architecture impact:** Consult with architect during quarterly reviews
- **Security escalations:** Contact CISO or security team immediately

---

**Version:** 1.0  
**Last Updated:** 2026-04-04  
**Next Review:** Quarterly (2026-07-04)
