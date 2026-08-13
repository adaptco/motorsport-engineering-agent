#!/bin/bash
set -euo pipefail

# Database backup script for mea-root-kernel
# Usage: ./backup.sh [environment]

ENVIRONMENT="${1:-staging}"
BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)-$ENVIRONMENT"
mkdir -p "$BACKUP_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Backup PostgreSQL
log_info "Backing up PostgreSQL database..."
if docker compose exec -T postgres pg_dump -U mea_prod mea_prod > "$BACKUP_DIR/postgres_dump.sql"; then
    log_info "✓ PostgreSQL backup completed: $BACKUP_DIR/postgres_dump.sql"
else
    log_warn "PostgreSQL backup failed"
fi

# Backup Redis
log_info "Backing up Redis database..."
if docker compose exec -T redis sh -lc 'redis-cli ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} BGSAVE'; then
    docker cp mea-redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb" 2>/dev/null || log_warn "Redis RDB copy failed"
    log_info "✓ Redis backup initiated: $BACKUP_DIR/redis_dump.rdb"
else
    log_warn "Redis backup failed"
fi

# Backup compose state
log_info "Backing up container state..."
docker compose ps > "$BACKUP_DIR/containers.log"
docker compose exec -T control_plane curl -s http://localhost:8000/healthz > "$BACKUP_DIR/control_plane_health.json" || true
docker compose exec -T mcp_server curl -s http://localhost:7000/healthz > "$BACKUP_DIR/mcp_server_health.json" || true

log_info "Backup completed: $BACKUP_DIR"
du -sh "$BACKUP_DIR"
