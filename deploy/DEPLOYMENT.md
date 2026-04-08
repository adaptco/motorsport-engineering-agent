# Deployment Pipeline Guide

This directory contains the complete deployment pipeline for the mea-root-kernel application.

## Directory Structure

```
deploy/
├── compose/              # Docker Compose environment overlays
│   ├── staging.yml      # Staging environment configuration
│   └── production.yml    # Production environment configuration
├── deploy.sh            # Main deployment script
├── rollback.sh          # Rollback script
├── backup.sh            # Database backup script
├── setup.sh             # Development environment setup
└── DEPLOYMENT.md        # This file
```

## Quick Start

### 1. Initial Setup

```bash
cd deploy
chmod +x *.sh
./setup.sh
```

This creates environment-specific `.env` files and log directories.

### 2. Deploy to Staging

```bash
./deploy.sh staging
```

### 3. Deploy to Production

```bash
./deploy.sh production
```

## Environment Configuration

Each environment has a Docker Compose overlay that extends the base `docker-compose.yml`:

### Development (docker-compose.yml)
- Used for local development
- Hot reload with volume mounts
- Debug logging enabled
- Lower resource limits

### Staging (staging.yml)
- Deployed from `main` branch
- Moderate resource limits
- Info-level logging
- Automatic health checks

### Production (production.yml)
- Deployed from version tags (`v*`)
- High resource limits
- Warning-level logging
- Multi-replica deployments (Compose deploy replicas)
- Secure credential handling

## Scripts

### deploy.sh
Main deployment script with full environment management.

**Usage:**
```bash
./deploy.sh [staging|production] [version]
```

**What it does:**
1. Validates environment and Docker daemon
2. Loads environment variables
3. Validates Docker Compose configuration
4. Creates backup of current state
5. Pulls latest images
6. Deploys services
7. Waits for services to be healthy
8. Runs database migrations
9. Performs health checks
10. Logs deployment summary

**Features:**
- Automatic backups before deployment
- Health checks for all services
- Database migration automation
- Colored output for readability
- Error handling and validation

### rollback.sh
Rollback to a previous backup.

**Usage:**
```bash
./rollback.sh <backup_directory> [environment]
```

**What it does:**
1. Stops current services
2. Restores database from backup (if available)
3. Restarts services
4. Restores previous state

### backup.sh
Create a full backup of current state.

**Usage:**
```bash
./backup.sh [environment]
```

**What it does:**
1. PostgreSQL dump to SQL file
2. Redis RDB backup
3. Container state logging
4. Health check snapshots

Backups are stored in `backups/<timestamp>-<environment>/`

### setup.sh
One-time setup for development environment.

**Usage:**
```bash
./setup.sh
```

Creates:
- Log directories
- `.env.dev`, `.env.staging`, `.env.production`
- Makes all scripts executable

## GitHub Actions CI/CD Pipeline

### Workflows

#### .github/workflows/deploy.yml
Automated deployment pipeline triggered on:
- Push to `main` (deploys to staging)
- Push of version tags `v*` (deploys to production)
- Manual workflow dispatch (choose environment)

**Features:**
- Multi-service Docker image builds
- Container registry push (GitHub Container Registry)
- Environment-specific deployments
- Automatic database migrations
- Deployment notifications

**Requirements:**
- `STAGING_DEPLOY_KEY`, `STAGING_HOST`, `STAGING_USER` secrets
- `PROD_DEPLOY_KEY`, `PROD_HOST`, `PROD_USER` secrets
- GitHub Container Registry access

#### .github/workflows/ci.yml
Continuous integration (already exists).

**What it does:**
- Runs Python tests
- Builds container images
- Validates code quality

#### .github/workflows/release-gate.yml
Release validation (already exists).

**What it does:**
- Validates version alignment
- Checks changelog
- Ensures CI passes

## Deployment Process

### Staging Deployment (Automatic)

1. Code pushed to `main` branch
2. CI tests run
3. Container images built and pushed to registry
4. Deploy workflow triggered
5. SSH to staging server
6. Pull latest code
7. Run `docker compose pull`
8. Run `docker compose up -d`
9. Run migrations
10. Health checks performed

### Production Deployment (Automatic)

1. Version tag pushed (e.g., `v0.3.5.1`)
2. Version alignment validated
3. CI tests run
4. Container images built and tagged
5. Deploy workflow triggered
6. SSH to production server
7. Checkout tag
8. Pull latest images
9. Run `docker compose up -d`
10. Run migrations
11. Health checks performed

## Security Considerations

### Credentials Management

- **Development**: Uses .env files (not in git)
- **Staging/Production**: Uses GitHub Actions secrets
- **SSH Keys**: Stored as GitHub Actions secrets
- **Database Passwords**: Environment variables, never hardcoded

### Image Security

- Images built and pushed to GitHub Container Registry
- Images tagged with git SHA for traceability
- Latest tags for production releases
- Image scanning recommended

### Database Access

- Migrations run post-deployment
- Connection pooling configured per environment
- Health checks validate database connectivity
- Backups automated before deployments

## Monitoring & Logs

View logs for services:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f control_plane

# From production host via SSH
ssh user@host "cd /opt/mea && docker compose logs -f control_plane"
```

Health check endpoints:
- Control Plane: `http://<host>:8000/health`
- MCP Server: `http://<host>:7000/health`

## Troubleshooting

### Service won't start
1. Check logs: `docker compose logs <service>`
2. Check health: `docker compose ps`
3. Validate environment variables: `docker compose config`
4. Check resource limits: `docker stats`

### Database migration failed
```bash
# Rollback migration
docker compose exec control_plane alembic downgrade -1

# Check migration status
docker compose exec control_plane alembic current

# Retry
docker compose exec control_plane alembic upgrade head
```

### Port conflicts
```bash
# Check what's using ports
lsof -i :8000
lsof -i :5432

# Or in Docker:
docker port <container>
```

### Need to rollback?
```bash
# List available backups
ls -lah backups/

# Rollback to specific backup
./rollback.sh backups/20240101-120000-staging staging
```

## Environment Variables Reference

### Common Variables (All Environments)
- `ENV`: Current environment (development/staging/production)
- `LOG_LEVEL`: Logging verbosity (debug/info/warning)
- `PYTHONUNBUFFERED`: Set to 1 for unbuffered output

### Database Variables
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password

### Redis Variables
- `REDIS_URL`: Redis connection string
- `REDIS_PASSWORD`: Redis password

### Application Variables
- `WORKERS`: Number of gunicorn workers
- `WORKER_CONCURRENCY`: Celery worker concurrency
- `DATABASE_POOL_SIZE`: Connection pool size

## Advanced Topics

### Multi-environment Deployments

Deploy different versions to different environments:

```bash
# Deploy specific version to staging
./deploy.sh staging v0.3.5

# Deploy latest to production
./deploy.sh production latest
```

### Blue-Green Deployment

For zero-downtime deployments, use:

```bash
# Start new version alongside current
docker compose -f docker-compose.yml -f deploy/compose/production.yml \
  -p mea-blue up -d

# Switch traffic (requires load balancer configuration)
# Then tear down old version
docker compose -p mea-green down
```

### Database Backup Strategy

Backups are created before every deployment. For additional safety:

```bash
# Manual backup
./backup.sh production

# Automatic scheduled backups (add to cron)
0 2 * * * cd /opt/mea && ./deploy/backup.sh production
```

## Version Information

Current version: See `VERSION.json` in project root

Version management:
1. Update `pyproject.toml` version
2. Update `VERSION.json`
3. Update `CHANGELOG.md`
4. Create git tag: `git tag v<major>.<minor>.<patch>`
5. Push tag: `git push origin v<major>.<minor>.<patch>`

## Support & Runbooks

For specific issues, see:
- Service startup issues: check docker logs
- Database connection issues: verify DATABASE_URL
- Performance issues: check resource limits and docker stats
- Security issues: review SECURITY.md
