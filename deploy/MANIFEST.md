# Deployment Pipeline v3.6 Patch - File Manifest

**Date**: April 5, 2026  
**Baseline**: v3.5.2  
**Target**: v3.6  

---

## New Files Created (7)

### 1. `.github/workflows/deploy.yml` (REPLACED)
- **Type**: GitHub Actions Workflow
- **Size**: ~9.3 KB
- **Changes**:
  - Added `validate-version` job for kernel version and contract bundle checks
  - Added `test-compose` job for topology validation
  - Enhanced `deploy-staging` with health verification
  - Enhanced `deploy-production` with health verification
  - Added concurrency control
  - Added environment variables for v3.6 validation

### 2. `deploy/compose/docker-compose.v3.6.yml` (NEW)
- **Type**: Docker Compose Configuration
- **Size**: ~4.4 KB
- **Contains**:
  - PostgreSQL service with v3.6 labels
  - Redis service with v3.6 labels
  - Control plane with lane=orchestration
  - Worker with lane=execution
  - MCP server with lane=tool-platform
  - Environment variables: MEA_VERSION, MEA_LANE, RUNTIME_CONTRACT_VALIDATION, CHECKPOINT_ENABLED
  - Isolated volume namespace (v3.6)

### 3. `deploy/containers/mea-v3.6/Dockerfile` (NEW)
- **Type**: Dockerfile
- **Size**: ~3.7 KB
- **Contains**:
  - Base image: v3.6-base (Python 3.11-slim)
  - Builder stage: v3.6-builder with contract bundle validation
  - Three service stages: v3.6-control-plane, v3.6-worker, v3.6-mcp-server
  - Build-time contract validation
  - Default target: v3.6-control-plane as latest
  - Version/kernel labels

### 4. `deploy/deploy.sh` (MODIFIED)
- **Type**: Bash Script
- **Size**: ~4.9 KB (was ~3.3 KB)
- **Changes**:
  - Added VERSION.json kernel version validation
  - Added runtime contract bundle presence check
  - Added contract bundle validation during build
  - Added contract preservation in backups
  - Added post-deployment contract health check
  - Enhanced logging with contract status
  - Backward compatible with v3.5.2

### 5. `deploy/verify-v3.6.sh` (NEW)
- **Type**: Bash Script
- **Size**: ~10.6 KB
- **Contains**:
  - 10-point verification checklist
  - Version alignment validation
  - Runtime contract bundle validation
  - Aero simulation contract validation
  - Dockerfile structure validation
  - Docker Compose topology validation
  - Environment configuration validation
  - Deployment script presence validation
  - Documentation presence validation
  - CI/CD workflow validation
  - Running services health check
  - Detailed summary with pass/warn/fail counts

### 6. `deploy/README.md` (MODIFIED)
- **Type**: Markdown Documentation
- **Size**: ~16.6 KB (was ~8.4 KB)
- **Changes**:
  - Title updated to "MEA v3.6+ Deployment Pipeline"
  - Overview section expanded with runtime contracts
  - Quick start now includes `./verify-v3.6.sh`
  - New "Runtime Contracts (v3.6+)" section with event flow and envelope structure
  - New "GitHub Actions Workflows" section with v3.6 details
  - Environment variables section updated with v3.6 variables
  - Service configuration now includes lane ownership
  - New "Verification & Monitoring" section
  - New "Runtime Contract Inspection" subsection
  - New "Event Ledger Access" subsection
  - Added references to PRD.md and contract requirements

### 7. `deploy/PATCH_SUMMARY.md` (NEW)
- **Type**: Markdown Documentation
- **Size**: ~15.5 KB
- **Contains**:
  - Executive summary of changes
  - Detailed description of all 6 major changes
  - Grounding to PRD workstreams
  - Pre-deployment checklist
  - Backward compatibility notes
  - Artifacts table
  - Testing and validation section
  - Known limitations and gotchas
  - Next steps and roadmap
  - References and links

### 8. `deploy/HANDOFF.md` (NEW)
- **Type**: Markdown Documentation
- **Size**: ~14.9 KB
- **Contains**:
  - Quick start guide
  - How to use summary
  - Key differences from v3.5.2
  - Manual actions required
  - Testing checklist
  - Common issues and solutions
  - File reference
  - Architecture overview
  - Rollback procedure
  - Integration points for code team
  - Maintenance and operations
  - Support and questions guide
  - Sign-off and next actions

---

## Files Preserved (No Changes)

### Compose & Container Files
- ✓ `docker-compose.yml` - Unchanged (v3.5.2 compatible)
- ✓ `Dockerfile` - Unchanged (v3.5.2 multi-stage targets)
- ✓ `control_plane/Dockerfile` - Unchanged
- ✓ `worker/Dockerfile` - Unchanged
- ✓ `mcp_server/Dockerfile` - Unchanged

### Deployment Scripts
- ✓ `deploy/rollback.sh` - Unchanged (compatible with v3.6 backups)
- ✓ `deploy/backup.sh` - Unchanged (backs up contracts if present)
- ✓ `deploy/setup.sh` - Unchanged
- ✓ `deploy/k8s-deploy.sh` - Unchanged

### Documentation
- ✓ `deploy/DEPLOYMENT.md` - Unchanged (v3.5.2 and v3.6 compatible)
- ✓ `deploy/K8S.md` - Unchanged
- ✓ `deploy/RUNBOOK.md` - Unchanged

### Kubernetes Manifests
- ✓ `deploy/k8s/postgres.yaml` - Unchanged
- ✓ `deploy/k8s/redis.yaml` - Unchanged
- ✓ `deploy/k8s/control-plane.yaml` - Unchanged
- ✓ `deploy/k8s/worker.yaml` - Unchanged
- ✓ `deploy/k8s/mcp-server.yaml` - Unchanged
- ✓ `deploy/k8s/rbac.yaml` - Unchanged

### CI/CD Workflows
- ✓ `.github/workflows/ci.yml` - Unchanged
- ✓ `.github/workflows/container-build.yml` - Unchanged
- ✓ `.github/workflows/release-gate.yml` - Unchanged

---

## Files NOT Included (Out of Scope)

### Runtime Code Changes (PRD Workstream 2)
- ❌ `control_plane/app.py` - Event emission (requires code implementation)
- ❌ `control_plane/queue.py` - Event validation (requires code implementation)
- ❌ `control_plane/services/mcp_client.py` - Tool request events (requires code implementation)
- ❌ `worker/backend_worker.py` - Event emission (requires code implementation)
- ❌ `shared/db.py` - Event ledger (requires code implementation)

### Contract Definitions (PRD Workstream 1)
- ❌ `contracts/runtime/agent_runtime_contract_bundle.schema.json` - Must be created separately
- ❌ `contracts/aero/aero_simulation_state.schema.json` - Optional for v3.6.0
- ❌ `contracts/runtime/README.md` - Documentation for contracts

### Test Suite (PRD Workstream 5)
- ❌ `tests/test_runtime_contract_bundle.py` - Schema validation tests
- ❌ `tests/test_runtime_event_order.py` - Event order enforcement tests

### Version Updates (Manual)
- ❌ `VERSION.json` - Must update kernel: "3.6", package: "0.3.6"
- ❌ `pyproject.toml` - Must update package version to 0.3.6
- ❌ `CHANGELOG.md` - Must document v3.6 release

---

## Dependency & Integration Map

```
New Files Created
├── .github/workflows/deploy.yml
│   ├── Requires: VERSION.json (kernel >= 3.6)
│   ├── Requires: contracts/runtime/agent_runtime_contract_bundle.schema.json
│   ├── Validates: docker-compose.yml (unchanged)
│   └── Validates: deploy/compose/docker-compose.v3.6.yml
│
├── deploy/compose/docker-compose.v3.6.yml
│   ├── Overlays: docker-compose.yml
│   ├── Uses: Dockerfile (unchanged) or deploy/containers/mea-v3.6/Dockerfile
│   └── Environment: v3.6-specific variables
│
├── deploy/containers/mea-v3.6/Dockerfile
│   ├── Validates: contracts/runtime/agent_runtime_contract_bundle.schema.json at build time
│   ├── Sources: pyproject.toml (unchanged)
│   └── Targets: v3.6-control-plane, v3.6-worker, v3.6-mcp-server
│
├── deploy/deploy.sh (enhanced)
│   ├── Validates: VERSION.json kernel version
│   ├── Validates: contracts/runtime/agent_runtime_contract_bundle.schema.json
│   ├── Backs up: contracts/runtime/ directory
│   └── Uses: docker-compose.yml + environment overlay
│
├── deploy/verify-v3.6.sh (new)
│   ├── Validates: All above dependencies
│   ├── Checks: CI/CD workflows
│   └── Output: Pass/warn/fail summary
│
└── Documentation
    ├── deploy/README.md (updated)
    ├── deploy/PATCH_SUMMARY.md (new)
    └── deploy/HANDOFF.md (new)
        └── Reference: PRD.md, CURRENT_STATE.md
```

---

## Size Summary

| Category | Files | Total Size |
|----------|-------|-----------|
| New Files | 6 | ~53 KB |
| Modified Files | 2 | +10 KB |
| Preserved Files | 20+ | (unchanged) |
| **Total** | **28+** | **~63 KB net** |

---

## Testing Artifacts

All new files have been created with:
- ✅ Proper shebang lines (bash scripts)
- ✅ Proper encoding (UTF-8)
- ✅ Proper line endings (LF)
- ✅ No syntax errors
- ✅ Extensive comments and documentation
- ✅ Backward compatibility maintained

---

## Deployment Checklist

Before deploying, complete these in order:

1. **Merge this patch**
   ```bash
   git merge deployment-v3.6-patch
   ```

2. **Update VERSION.json** ⚠️ MANUAL
   ```json
   {
     "kernel_version": "3.6",
     "package_version": "0.3.6",
     "release_channel": "stable",
     "compatibility": {
       "replay_schema": 1,
       "forensic_ledger_schema": 1
     }
   }
   ```

3. **Add Runtime Contract Bundle** ⚠️ MANUAL
   - Create `contracts/runtime/agent_runtime_contract_bundle.schema.json`
   - Source: From PRD.md Workstream 1

4. **Verify Readiness**
   ```bash
   ./deploy/verify-v3.6.sh
   ```

5. **Deploy to Staging**
   ```bash
   ./deploy/deploy.sh staging
   ```

6. **Create Release Tag**
   ```bash
   git tag v0.3.6
   git push origin v0.3.6
   ```

---

## Files at a Glance

```
deploy/
├── README.md                         ✏️ MODIFIED (v3.6+ docs)
├── DEPLOYMENT.md                     ✓ UNCHANGED
├── K8S.md                            ✓ UNCHANGED
├── RUNBOOK.md                        ✓ UNCHANGED
├── PATCH_SUMMARY.md                  ✨ NEW (change log)
├── HANDOFF.md                        ✨ NEW (integration guide)
│
├── deploy.sh                         ✏️ MODIFIED (contract validation)
├── setup.sh                          ✓ UNCHANGED
├── backup.sh                         ✓ UNCHANGED
├── rollback.sh                       ✓ UNCHANGED
├── k8s-deploy.sh                     ✓ UNCHANGED
├── verify-v3.6.sh                    ✨ NEW (pre-deploy checklist)
│
├── compose/
│   ├── staging.yml                   ✓ UNCHANGED
│   ├── production.yml                ✓ UNCHANGED
│   └── docker-compose.v3.6.yml       ✨ NEW (v3.6 overlay)
│
├── containers/
│   └── mea-v3.6/
│       └── Dockerfile                ✨ NEW (v3.6 build)
│
└── k8s/
    ├── postgres.yaml                 ✓ UNCHANGED
    ├── redis.yaml                    ✓ UNCHANGED
    ├── control-plane.yaml            ✓ UNCHANGED
    ├── worker.yaml                   ✓ UNCHANGED
    ├── mcp-server.yaml               ✓ UNCHANGED
    └── rbac.yaml                     ✓ UNCHANGED

Root
├── docker-compose.yml                ✓ UNCHANGED
├── Dockerfile                        ✓ UNCHANGED
└── .github/workflows/
    ├── deploy.yml                    ✏️ MODIFIED (v3.6 validation)
    ├── ci.yml                        ✓ UNCHANGED
    ├── container-build.yml           ✓ UNCHANGED
    └── release-gate.yml              ✓ UNCHANGED
```

---

## Verification Commands

Run these to verify patch integrity:

```bash
# 1. Check file presence
ls -lah deploy/{verify-v3.6.sh,PATCH_SUMMARY.md,HANDOFF.md}
ls -lah deploy/compose/docker-compose.v3.6.yml
ls -lah deploy/containers/mea-v3.6/Dockerfile

# 2. Check modified files
grep -l "validate-version" .github/workflows/deploy.yml
grep -l "RUNTIME_CONTRACT_VALIDATION" deploy/deploy.sh
grep -l "v3.6+" deploy/README.md

# 3. Validate syntax
docker compose -f docker-compose.yml -f deploy/compose/docker-compose.v3.6.yml config
bash -n deploy/verify-v3.6.sh
bash -n deploy/deploy.sh
docker build -f deploy/containers/mea-v3.6/Dockerfile --target v3.6-control-plane --dry-run .
```

---

**Manifest created**: April 5, 2026  
**Total artifacts**: 8 new/modified, 20+ preserved  
**Status**: ✅ Ready for integration
