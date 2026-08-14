#!/bin/bash
set -euo pipefail

# Deployment script for mea-root-kernel v3.8+
# Usage: ./deploy.sh [staging|production] [version]
# Validates runtime contracts before deployment

ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-adaptco/motorsport-engineering-agent}"
export REGISTRY IMAGE_NAME VERSION

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

log_info "Starting deployment to $ENVIRONMENT environment with version $VERSION"
log_info "Using image registry: ${REGISTRY}/${IMAGE_NAME}"

# Check Docker daemon
if ! docker ps > /dev/null 2>&1; then
    log_error "Docker daemon is not running"
    exit 1
fi

# Load environment-specific .env file
if [ -f ".env.$ENVIRONMENT" ]; then
    log_info "Loading environment variables from .env.$ENVIRONMENT"
    set -a
    source ".env.$ENVIRONMENT"
    set +a
else
    log_warn ".env.$ENVIRONMENT not found. Using defaults."
fi

# ============================================================
# V3.8+ Contract Validation
# ============================================================
log_info "Validating v3.8 runtime contracts..."

if [ ! -f "contracts/runtime/agent_runtime_contract_bundle.schema.json" ]; then
    log_warn "Runtime contract bundle not found. Aero contracts are optional for v3.8.0."
fi

# Validate VERSION.json kernel version
kernel_version=$(python -c "import json; print(json.load(open('VERSION.json'))['kernel_version'])" 2>/dev/null || echo "")
if [ -z "$kernel_version" ]; then
    log_error "Could not read kernel version from VERSION.json"
    exit 1
fi

log_info "Kernel version: $kernel_version"
if [[ "$kernel_version" != "3.8" ]]; then
    log_error "Expected kernel version 3.8, found $kernel_version."
    exit 1
fi

# Pull latest images for the target environment overlay
log_info "Pulling latest images..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" pull

# Validate compose files
log_info "Validating docker-compose configuration..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" config > /dev/null

# Additional v3.8 compose validation if available
if [ -f "deploy/compose/docker-compose.v3.8.yml" ]; then
    log_info "Validating v3.8 compose topology..."
    docker compose -f docker-compose.yml -f deploy/compose/docker-compose.v3.8.yml config > /dev/null
    log_info "✓ v3.8 compose topology valid"
fi

# Backup current state
BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
log_info "Backing up current state to $BACKUP_DIR"

docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" ps > "$BACKUP_DIR/containers.log" || true
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" logs > "$BACKUP_DIR/logs.log" 2>&1 || true

# Preserve runtime contract bundle in backup
if [ -d "contracts/runtime" ]; then
    cp -r contracts/runtime "$BACKUP_DIR/runtime_contracts" || true
fi

# Deploy services
log_info "Deploying services..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" up -d

# Wait for services to be healthy
log_info "Waiting for services to become healthy..."
for i in {1..30}; do
    if docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T postgres pg_isready -U "${POSTGRES_USER:-mea}" > /dev/null 2>&1; then
        log_info "✓ PostgreSQL is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "PostgreSQL failed to become healthy"
        exit 1
    fi
    echo -n "."
    sleep 2
done

for i in {1..30}; do
    if [ -n "${REDIS_PASSWORD:-}" ]; then
        if docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T -e REDISCLI_AUTH="$REDIS_PASSWORD" redis redis-cli ping > /dev/null 2>&1; then
            log_info "✓ Redis is healthy"
            break
        fi
    elif docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Redis failed to become healthy"
        exit 1
    fi
    echo -n "."
    sleep 2
done

# Run database migrations
log_info "Running database migrations..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T control_plane alembic upgrade head || {
    log_error "Database migration failed"
    exit 1
}

# Health check
log_info "Performing health checks..."
if docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T control_plane curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    log_info "✓ Control plane is healthy"
else
    log_error "Control plane health check failed"
    exit 1
fi

# Check runtime contract validation (v3.8+)
if docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T control_plane curl -f http://localhost:8000/healthz/dependencies 2>/dev/null | grep -q '"contracts"'; then
    log_info "✓ Runtime contracts accessible"
fi

if docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" exec -T mcp_server curl -f http://localhost:7000/healthz > /dev/null 2>&1; then
    log_info "✓ MCP server is healthy"
else
    log_warn "MCP server health check failed (may still be starting)"
fi

log_info "Deployment to $ENVIRONMENT completed successfully!"
log_info "Backup saved to $BACKUP_DIR"

# Summary
log_info "Current deployment status:"
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" ps
log_info "Kernel version: $kernel_version"
log_info "Environment: $ENVIRONMENT"
log_info "Timestamp: $(date -u)"
