# Progress Tracking - Motorsport Engineering Agent

**Document Version:** 1.1  
**Last Updated:** 2026-04-05  
**Status:** 🟡 AUDIT REFRESH COMPLETE (PRD gap index + Actions pass checklist updated)  
**Reference:** [PRD.md](./PRD.md)

---

## 1) Persistent Workflow Memory Context

- Installed skill: `notion-knowledge-capture`
- Install path: `~/.codex/skills/notion-knowledge-capture`
- Notes:
  - No upstream curated skill named `persistent-workflow-memory` was available.
  - `notion-knowledge-capture` is the closest persistent-memory workflow skill for reusable agent context capture.

---

## 2) Repository Review Source

- Local repo audited: `origin https://github.com/adaptco/motorsport-engineering-agent.git`
- GitHub app connector lookup for installed repos returned no entry for this repo in this session, so indexing was performed from the local working tree.

---

## 3) PRD Required Files/Modules Index (Current State)

### Present

- `control_plane/app.py`
- `worker/backend_worker.py`
- `worker/github_app_client.py`
- `mcp_server/app.py`
- `shared/models.py`
- `shared/forensic_ledger.py`
- `docs/supervisor-loop.md`
- `db/migrations/001_init.sql`
- `db/migrations/002_session_runtime.sql`
- `db/migrations/003_evidence_packets.sql`
- `.github/workflows/ci.yml`
- `README.md`

### Missing (Referenced by PRD / review criteria)

- `control_plane/config.py`
- `mea/policy_engine.py`
- `tests/conftest.py`
- `CONTRIBUTING.md`
- `docs/DEPLOYMENT.md`

---

## 4) Actions Workflow Status (Current)

### `.github/workflows/ci.yml`

- Structurally valid YAML.
- Matches unit checks in `tests/test_ci_workflow.py`:
  - `actions/checkout@v6`
  - `actions/setup-node@v6` with Node `24`
  - `actions/setup-python@v6` with Python `3.13`
- Builds Docker images for control plane / mcp server / worker after tests.

### `.github/workflows/release-gate.yml`

- File exists but contains multiple blocking errors that will fail workflow execution:
  - Invalid action ref: `actions/checkout@3v4`
  - Invalid Python module in inline script: `tomllab` (should be `tomllib`)
  - Broken bash/script syntax in changelog extraction and expected header interpolation
  - Broken JavaScript in `actions/github-script` step (e.g., `return 4byName;`)

---

## 5) What Must Be Created To Satisfy PRD + Stabilize Test/CI Readiness

### Create now

1. `tests/conftest.py`  
   Centralized fixtures + deterministic shared setup for test infrastructure consistency.

2. `control_plane/config.py`  
   Explicit config module expected by PRD architecture/documentation model.

3. `mea/policy_engine.py`  
   Canonical policy engine module path referenced by PRD tasks.

4. `docs/DEPLOYMENT.md`  
   Deployment/run instructions required by PRD documentation acceptance criteria.

5. `CONTRIBUTING.md`  
   Contributor workflow and quality gates required by PRD documentation completeness.

### Fix (not create) to get Actions green

1. Correct `.github/workflows/release-gate.yml` syntax and logic errors listed above.
2. Ensure release-gate expected changelog/version checks use valid expressions.
3. Re-run CI + release-gate workflows after patching.

---

## 6) Current Overall Status

- Review artifacts are present, but the progress tracker was previously inconsistent/outdated.
- PRD still has explicit missing file/module targets (listed above).
- Main CI workflow appears aligned with tests; release-gate workflow needs immediate correction before reliable Actions pass status can be claimed.
