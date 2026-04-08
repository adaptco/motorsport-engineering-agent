# MEA Deployment Pipeline

Complete deployment pipeline for the mea-root-kernel application supporting Docker Compose and Kubernetes deployments.

## Overview

This deployment system provides:

- **CI/CD Automation**: GitHub Actions workflows for automated testing, building, and deployment
- **Multi-Environment Support**: Development, staging, and production deployments
- **Docker Compose**: Local development and simple deployments
- **Kubernetes**: Production-grade deployments with auto-scaling, health checks, and high availability
- **Backup & Recovery**: Automated backups and rollback capabilities
- **Health Monitoring**: Built-in health checks and status monitoring

## Quick Start

### 1. Docker Compose (Development/Small Deployments)

```bash
# Initial setup
./setup.sh

# Deploy to staging
./deploy.sh staging

# Deploy to production
./deploy.sh production
```

### 2. Kubernetes (Production)

```bash
# Deploy to cluster
./k8s-deploy.sh minikube default

# Monitor deployment
kubectl get pods -w

# Forward ports for testing
kubectl port-forward svc/control-plane 8000:8000
```

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker Compose deployment guide, scripts, and operations
- **[K8S.md](K8S.md)** - Kubernetes deployment, scaling, monitoring, and troubleshooting

## Directory Structure

```
deploy/
├── compose/                    # Docker Compose environment overlays
│   ├── staging.yml            # Staging configuration
│   └── production.yml         # Production configuration
│
├── k8s/                       # Kubernetes manifests
│   ├── postgres.yaml          # PostgreSQL StatefulSet
│   ├── redis.yaml             # Redis StatefulSet
│   ├── control-plane.yaml     # Control plane Deployment
│   ├── worker.yaml            # Worker Deployment
│   ├── mcp-server.yaml        # MCP server Deployment
│   └── rbac.yaml              # RBAC and PodDisruptionBudgets
│
├── deploy.sh                  # Main deployment script (Docker Compose)
├── rollback.sh                # Rollback script
├── backup.sh                  # Backup script
├── setup.sh                   # Development environment setup
├── k8s-deploy.sh              # Kubernetes deployment script
│
└── DEPLOYMENT.md              # Docker Compose guide
└── K8S.md                     # Kubernetes guide
```

## GitHub Actions Workflows

### deploy.yml
Automated deployment pipeline triggered by:
- Push to `main` → deploys to staging
- Push of version tags `v*` → deploys to production
- Manual workflow dispatch

**Status Checks:**
- version-alignment: Validates VERSION.json, pyproject.toml, and CHANGELOG.md
- required-ci-checks: Waits for test and build-images jobs to pass
- build-and-push: Builds and pushes Docker images to registry
- deploy-staging: Deploys to staging environment
- deploy-production: Deploys to production environment

## Environment Variables

### Common (All Environments)
- `ENV`: Current environment (development/staging/production)
- `LOG_LEVEL`: Logging verbosity (debug/info/warning)
- `PYTHONUNBUFFERED`: Set to 1 for unbuffered output

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
- `WORKER_CONCURRENCY`: Celery/task queue concurrency
- `DATABASE_POOL_SIZE`: Connection pool size

## Key Scripts

### deploy.sh
Deploy services with automatic backups and health checks.

```bash
./deploy.sh [staging|production] [version]
```

Features:
- Automatic environment validation
- Pre-deployment backups
- Service health checks
- Database migrations
- Deployment logging

### rollback.sh
Restore from a previous backup.

```bash
./rollback.sh <backup_directory> [environment]
```

### backup.sh
Create a full backup of current state.

```bash
./backup.sh [environment]
```

Creates:
- PostgreSQL dump
- Redis RDB backup
- Container state logs
- Health check snapshots

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

### Control Plane
- **Port**: 8000
- **Health Check**: /health endpoint
- **Replicas**: 2 (staging/production)
- **CPU**: 0.5-2 cores
- **Memory**: 512MB-2GB

### Worker
- **Replicas**: 3 (staging) / 3+ (production)
- **CPU**: 1-4 cores
- **Memory**: 1GB-4GB
- **Concurrency**: Scales with load

### MCP Server
- **Port**: 7000
- **Health Check**: /health endpoint
- **Replicas**: 2
- **CPU**: 0.5-2 cores
- **Memory**: 512MB-2GB

### PostgreSQL
- **Port**: 5432
- **Storage**: Persistent volume
- **Backups**: Automated before deployments

### Redis
- **Port**: 6379
- **Storage**: Persistent volume
- **Persistence**: AOF enabled

## Deployment Strategies

### Staging (Automatic on main branch)
1. Push to main triggers CI
2. Tests and image builds complete
3. Images pushed to registry
4. Staging environment updated
5. Health checks performed

### Production (Automatic on version tags)
1. Create version tag: `git tag v0.3.5.1`
2. Push tag triggers version validation
3. Tests run
4. Images built and tagged
5. Production environment updated
6. Database migrations run
7. Health checks performed

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
```

### Rollback if Needed
```bash
# Find backup
ls backups/

# Rollback to specific backup
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

### Database Access
- Connection pooling configured
- Credentials in environment variables
- Automated backups before changes
- Connection limits per environment

## Advanced Topics

### Blue-Green Deployment
For zero-downtime updates:

```bash
# Start new version
docker compose -p mea-blue up -d

# Switch traffic (requires load balancer)
# Tear down old version
docker compose -p mea-green down
```

### Custom Environment
To add a new environment (e.g., integration):

1. Create `deploy/compose/integration.yml`
2. Add secrets to GitHub Actions
3. Add deployment job to `.github/workflows/deploy.yml`
4. Update scripts to support new environment

### Horizontal Pod Autoscaler (Kubernetes)
Automatic scaling based on metrics:

```bash
# View HPA status
kubectl get hpa

# Modify HPA
kubectl edit hpa control-plane-hpa
```

## Performance Tuning

### Database Connection Pool
Increase `DATABASE_POOL_SIZE` for high-concurrency workloads:

```bash
# Edit environment variable
kubectl set env deployment/control-plane DATABASE_POOL_SIZE=50
```

### Worker Concurrency
Adjust `WORKER_CONCURRENCY` based on CPU cores:

```bash
# Example: 8 worker processes with 4 tasks each
kubectl set env deployment/worker WORKER_CONCURRENCY=32
```

### Gunicorn Workers
Update `WORKERS` for control plane:

```bash
# 4 workers for 4-core system
kubectl set env deployment/control-plane WORKERS=4
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/reference/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

## Support

For deployment issues:
1. Check logs: `docker compose logs` or `kubectl logs`
2. Review backups: `ls -lah backups/`
3. Check configuration: `docker compose config`
4. Verify health: `curl http://localhost:8000/health`

## Version

Current version: See VERSION.json in project root

Release process:
1. Update VERSION.json
2. Update CHANGELOG.md
3. Create git tag: `git tag v<major>.<minor>.<patch>`
4. Push tag to trigger automated deployment
