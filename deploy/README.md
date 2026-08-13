# MEA v3.6+ Deployment Pipeline

Complete deployment pipeline for the mea-root-kernel v3.6+ application with runtime contracts, checkpoint resumption, and enforceable event gates. Supports Docker Compose and Kubernetes deployments.

## Overview

This deployment system provides v3.6+ runtime contract validation, checkpoint-based resumption, and deterministic event ordering:

- **Runtime Contracts**: Enforced event gates (`request.received → run.created → workflow.policy.screened → ... → run.completed`)
- **CI/CD Automation**: GitHub Actions workflows with version and contract validation
- **Multi-Environment Support**: Development, staging, and production deployments
- **Docker Compose**: Local development and simple deployments with v3.6 topology overlay
- **Kubernetes**: Production-grade deployments with auto-scaling, health checks, and high availability
- **Backup & Recovery**: Automated backups and rollback capabilities with contract preservation
- **Health Monitoring**: Built-in health checks, runtime contract validation, and status monitoring

## Quick Start

### 1. Verify v3.6 Deployment Readiness

```bash
# Run comprehensive v3.6 checks
./verify-v3.6.sh
```

This validates:
- Runtime contract bundle presence and validity
- Aero simulation contracts (optional)
- Dockerfile multi-stage targets
- Docker Compose topology alignment
- Environment-specific overrides
- CI/CD workflow configuration

### 2. Docker Compose Deployment

```bash
# Initial setup
./setup.sh

# Deploy to staging with runtime contract validation
./deploy.sh staging

# Deploy to production
./deploy.sh production v0.3.6
```

### 3. v3.6 Topology (Optional)

```bash
# Deploy with v3.6-specific compose overlay
docker compose -f docker-compose.yml -f deploy/compose/docker-compose.v3.6.yml up -d
```

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker Compose deployment guide, scripts, and operations
- **[K8S.md](K8S.md)** - Kubernetes deployment, scaling, monitoring, and troubleshooting

## Directory Structure

```
deploy/
├── compose/                              # Docker Compose environment overlays
│   ├── staging.yml                      # Staging configuration
│   ├── production.yml                   # Production configuration
│   └── docker-compose.v3.6.yml          # v3.6 topology overlay (NEW)
│
├── containers/
│   └── mea-v3.6/                        # v3.6 container definitions (NEW)
│       └── Dockerfile                   # Multi-stage v3.6 build
│
├── k8s/                                 # Kubernetes manifests
│   ├── postgres.yaml                    # PostgreSQL StatefulSet
│   ├── redis.yaml                       # Redis StatefulSet
│   ├── control-plane.yaml               # Control plane Deployment
│   ├── worker.yaml                      # Worker Deployment
│   ├── mcp-server.yaml                  # MCP server Deployment
│   └── rbac.yaml                        # RBAC and PodDisruptionBudgets
│
├── deploy.sh                            # Main deployment script (v3.6+ aware)
├── rollback.sh                          # Rollback script
├── backup.sh                            # Backup script
├── setup.sh                             # Development environment setup
├── k8s-deploy.sh                        # Kubernetes deployment script
├── verify-v3.6.sh                       # v3.6 verification checklist (NEW)
│
├── README.md                            # This file
├── DEPLOYMENT.md                        # Detailed Docker Compose guide
├── K8S.md                               # Kubernetes guide
└── RUNBOOK.md                           # Operations and troubleshooting
```

## Runtime Contracts (v3.6+)

The v3.6 deployment enforces a runtime contract bundle for deterministic execution and audit:

### Required Contract Bundle

Location: `contracts/runtime/agent_runtime_contract_bundle.schema.json`

**Enforced Event Sequence:**
```
request.received
  ↓
run.created
  ↓
workflow.policy.screened
  ↓
plan.proposed / plan.repaired / plan.failed
  ↓
step.dispatched
  ↓
tool.requested / approval.resolved
  ↓
tool.executed / action.proposed / action.repaired / action.invalid
  ↓
state.transitioned
  ↓
checkpoint.persisted
  ↓
run.completed / run.failed
```

**Envelope Structure (All Events):**
- `event_type`: Event classification (string)
- `schema_version`: Contract version (integer)
- `event_id`: Unique event identifier (UUID)
- `run_id`: Run context (UUID)
- `task_id`: Task context (UUID)
- `step_id`: Step context (UUID)
- `created_at`: Timestamp (ISO 8601)
- `lane`: Execution lane (UI, ORCH, GOV, CTX, LLM, RT, MCP, EXT, HITL, OBS)
- `fsm_state`: Finite state machine state (string)
- `prev_hash`: Previous state hash (SHA256 hex)
- `state_hash`: Current state hash (SHA256 hex)
- `policy_version`: Policy version applied (string)
- `payload`: Event-specific payload (object)

**Key Contracts:**
- `tool.requested` carries `idempotency_key` for replay safety
- `plan.repaired` and `action.repaired` carry `repair_metadata`
- `checkpoint.persisted` enables resumable execution
- `run.failed` includes `failure_code` and `error_context`

### Aero Simulation Contracts (Optional for v3.6.0)

Location: `contracts/aero/aero_simulation_state.schema.json`

**Durable State Model:**
- Vehicle identity and geometry state
- Solver configuration and execution history
- CL/CD branch proposals with evaluation results
- Provenance and state hashes for audit
- Telemetry reference links (non-embedded)

**Pre-Deployment Check:**
- Deployment scripts validate runtime contract bundle presence
- Aero contracts are optional but validated if present
- GitHub Actions workflow includes contract validation step

## GitHub Actions Workflows

### deploy.yml (v3.6+ Enhanced)

Automated deployment pipeline triggered by:
- Push to `main` → deploys to staging
- Push of version tags `v*` → deploys to production
- Manual workflow dispatch

**v3.6+ Enhancements:**
- `validate-version` job: Checks kernel version ≥ 3.6, validates contract bundle
- `test-compose` job: Validates Docker Compose topology with v3.6 overlays
- Contract preservation: Backups include runtime contracts
- Health verification: Post-deployment contract validation checks

**Status Checks:**
- validate-version: Kernel version >= 3.6 + contract bundle presence
- test-compose: Docker Compose configuration + v3.6 overlay validation
- build-and-push: Builds and pushes Docker images
- deploy-staging: Deploys to staging with contract validation
- deploy-production: Deploys to production with version tag + contract validation

## Environment Variables

### Common (All Environments)
- `ENV`: Current environment (development/staging/production)
- `LOG_LEVEL`: Logging verbosity (debug/info/warning)
- `PYTHONUNBUFFERED`: Set to 1 for unbuffered output
- `MEA_VERSION`: Current v3.6+ version
- `MEA_KERNEL_VERSION`: Current kernel version (3.6+)
- `RUNTIME_CONTRACT_VALIDATION`: Enable runtime event validation (true)
- `CHECKPOINT_ENABLED`: Enable checkpoint persistence (true)

### Database
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

### Redis
- `REDIS_URL`: Redis connection string
- `REDIS_PASSWORD`: Redis password

### Application
- `WORKERS`: Number of gunicorn workers
- `WORKER_CONCURRENCY`: Task queue concurrency (execution lane)
- `DATABASE_POOL_SIZE`: Connection pool size

## Key Scripts

### verify-v3.6.sh (NEW)
Comprehensive v3.6 deployment readiness verification.

```bash
./verify-v3.6.sh
```

Validates:
- Version alignment (kernel 3.6+, package 0.3.6+)
- Runtime contract bundle presence and JSON validity
- Aero simulation contracts (optional)
- Dockerfile multi-stage targets
- Docker Compose topology alignment
- Environment-specific overrides
- Deployment scripts present
- CI/CD workflows configured
- Running services health (if deployed)

### deploy.sh (v3.6+ Enhanced)
Deploy services with automatic backups and health checks.

```bash
./deploy.sh [staging|production] [version]
```

**v3.6+ Enhancements:**
- Contract bundle validation before deployment
- VERSION.json kernel version check
- Contract preservation in backups
- Runtime contract accessibility validation
- Post-deployment contract health check

### rollback.sh
Restore from a previous backup.

```bash
./rollback.sh <backup_directory> [environment]
```

Restores:
- Database state (if backup available)
- Container configuration
- Runtime contracts (if backed up)

### backup.sh
Create a full backup of current state.

```bash
./backup.sh [environment]
```

Backs up:
- PostgreSQL dump
- Redis RDB backup
- Container state logs
- Health check snapshots
- Runtime contracts (if present)

### setup.sh
One-time development environment setup.

```bash
./setup.sh
```

Creates:
- Log directories
- Environment-specific .env files
- Makes scripts executable

## Service Configuration

### Control Plane (Orchestration Lane)
- **Port**: 8000
- **Health Check**: `/healthz` endpoint
- **Replicas**: 2 (staging/production)
- **CPU**: 0.5-2 cores
- **Memory**: 512MB-2GB
- **Lane**: orchestration
- **Responsibilities**: Request validation, policy screening, workflow orchestration, event emission

### Worker (Execution Lane)
- **Replicas**: 3 (staging) / 3+ (production)
- **CPU**: 1-4 cores
- **Memory**: 1GB-4GB
- **Lane**: execution
- **Concurrency**: Configurable via `WORKER_CONCURRENCY`
- **Responsibilities**: Task execution, runtime event emission, checkpoint persistence, state transitions

### MCP Server (Tool/Capability Platform Lane)
- **Port**: 7000
- **Health Check**: `/healthz` endpoint
- **Replicas**: 2
- **CPU**: 0.5-2 cores
- **Memory**: 512MB-2GB
- **Lane**: tool-platform
- **MCP Version**: 1.0
- **Responsibilities**: Controlled tool and action surface, MCP v1 routing

### PostgreSQL (Data Plane)
- **Port**: 5432
- **Storage**: Persistent volume
- **Backups**: Automated before deployments
- **Responsibilities**: Runtime state, event ledger, checkpoint persistence

### Redis (Data Plane)
- **Port**: 6379
- **Storage**: Persistent volume (AOF)
- **Persistence**: everysec
- **Responsibilities**: Task queue, state caching, checkpoint staging

## Deployment Strategies

### Staging (Automatic on main branch)
1. Push to main triggers CI
2. Version validation (3.6+)
3. Contract bundle presence check
4. Tests and image builds complete
5. Images pushed to registry
6. Staging environment updated
7. Contract validation performed
8. Health checks performed

### Production (Automatic on version tags)
1. Create version tag: `git tag v0.3.6`
2. Push tag triggers version validation
3. Contract bundle validation
4. Tests run
5. Images built and tagged
6. Production environment updated
7. Database migrations run
8. Contract health check performed
9. Health checks performed

## Verification & Monitoring

### Pre-Deployment

```bash
# Run verification suite
./verify-v3.6.sh

# Validate specific component
docker compose -f docker-compose.yml -f deploy/compose/docker-compose.v3.6.yml config
```

### Post-Deployment

```bash
# Check control plane health
curl http://localhost:8000/healthz
curl http://localhost:8000/healthz/dependencies

# Check MCP server health
curl http://localhost:7000/healthz

# View logs with contract trace
docker compose logs -f control_plane | grep -i "contract\|event"
docker compose logs -f worker | grep -i "contract\|checkpoint"
```

### Contract Validation

```bash
# Verify contract bundle in deployment
docker compose exec control_plane curl -f http://localhost:8000/contracts

# Test event emission path
docker compose exec worker python -m worker.contracts.validate_bundle
```

## Monitoring & Troubleshooting

### Check Status
```bash
# Docker Compose
docker compose ps
docker compose logs -f control_plane

# Kubernetes
kubectl get pods -o wide
kubectl logs -f deployment/control-plane
```

### View Backups
```bash
ls -lah backups/
du -sh backups/*

# Check contract preservation in backups
ls -lah backups/*/runtime_contracts/
```

### Rollback if Needed
```bash
# Find backup
ls backups/

# Rollback to specific backup (contracts included)
./rollback.sh backups/20240115-143000-production production
```

## Security

### Secrets Management
- Development: .env files (not in git)
- GitHub Actions: Secrets stored in GitHub
- Kubernetes: Secrets objects with RBAC

### Image Security
- Images built from trusted base images
- Non-root user (UID 5678)
- Read-only root filesystem (Kubernetes)
- Security contexts enforced
- Network policies (Kubernetes)

### Contract Security
- Runtime contracts immutable after validation
- Event signatures (optional): SHA256 state hashes
- Audit trail: Complete event ledger persisted
- Replay protection: idempotency_key in tool.requested

### Database Access
- Connection pooling configured
- Credentials in environment variables
- Automated backups before changes
- Connection limits per environment

## Advanced Topics

### Blue-Green Deployment
For zero-downtime updates with contract validation:

```bash
# Start new v3.6 version
docker compose -p mea-blue -f docker-compose.yml -f deploy/compose/docker-compose.v3.6.yml up -d

# Verify contract validation
docker compose -p mea-blue exec control_plane curl -f http://localhost:8000/contracts

# Switch traffic (requires load balancer)
# Tear down old version
docker compose -p mea-green down
```

### Custom Environment
To add a new environment (e.g., integration):

1. Create `deploy/compose/integration.yml`
2. Add secrets to GitHub Actions
3. Add deployment job to `.github/workflows/deploy.yml`
4. Update `verify-v3.6.sh` to include new environment
5. Run verification suite

### Runtime Contract Inspection
Access deployed contracts at runtime:

```bash
# View contract bundle
curl -s http://localhost:8000/contracts | jq .

# View aero contracts (if deployed)
curl -s http://localhost:8000/contracts/aero | jq .
```

### Event Ledger Access
Inspect emitted events for audit/replay:

```bash
# Query event ledger
docker compose exec postgres psql -U mea -d mea -c "SELECT * FROM runtime_events ORDER BY created_at DESC LIMIT 10;"

# Export event ledger for analysis
docker compose exec postgres pg_dump -U mea -d mea -t runtime_events > event_ledger.sql
```

## Performance Tuning

### Database Connection Pool
Increase `DATABASE_POOL_SIZE` for high-concurrency workloads:

```bash
# Edit environment variable
docker compose exec -e DATABASE_POOL_SIZE=50 control_plane
```

### Worker Concurrency
Adjust `WORKER_CONCURRENCY` based on CPU cores and task profile:

```bash
# Example: 8 worker processes with 4 tasks each
docker compose exec -e WORKER_CONCURRENCY=32 worker
```

### Gunicorn Workers
Update `WORKERS` for control plane:

```bash
# 4 workers for 4-core system
docker compose exec -e WORKERS=4 control_plane
```

### Event Ledger Retention
Manage event ledger size via retention policy:

```bash
# Archive old events (example)
docker compose exec postgres psql -U mea -d mea -c "DELETE FROM runtime_events WHERE created_at < NOW() - INTERVAL '90 days';"
```

## Resources

- [PRD.md](../../PRD.md) - Product requirements and feature roadmap
- [VERSION.json](../../VERSION.json) - Current version and compatibility
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/reference/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

## Support

For deployment issues:
1. Run verification: `./verify-v3.6.sh`
2. Check logs: `docker compose logs` or `kubectl logs`
3. Review backups: `ls -lah backups/`
4. Check configuration: `docker compose config`
5. Verify contracts: `curl http://localhost:8000/contracts`
6. Verify health: `curl http://localhost:8000/healthz`

## Version

Current version: See VERSION.json in project root

**v3.6+ Requirements:**
- Kernel version must be 3.6 or higher
- Runtime contract bundle must be present in `contracts/runtime/`
- Docker Compose uses multi-environment overlays
- All events must comply with runtime contract schema

Release process:
1. Update VERSION.json (kernel: 3.6+, package: 0.3.6+)
2. Validate runtime contracts in `contracts/runtime/`
3. Update CHANGELOG.md
4. Run `./verify-v3.6.sh` to confirm readiness
5. Create git tag: `git tag v0.3.6` (example)
6. Push tag to trigger automated deployment with contract validation
