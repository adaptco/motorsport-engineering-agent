#!/bin/bash
set -euo pipefail

# Rollback script for mea-root-kernel application
# Usage: ./rollback.sh [backup_path]

BACKUP_PATH="${1:-.}"
ENVIRONMENT="${2:-staging}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ ! -d "$BACKUP_PATH" ] || [ ! -f "$BACKUP_PATH/containers.log" ]; then
    log_error "Invalid backup path: $BACKUP_PATH"
    echo "Usage: ./rollback.sh <backup_directory>"
    exit 1
fi

log_warn "Rolling back to backup from $BACKUP_PATH"
read -p "Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_info "Rollback cancelled"
    exit 0
fi

# Stop current deployment
log_info "Stopping current services..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" down

# Restore from backup (if database backup exists)
if [ -f "$BACKUP_PATH/postgres_dump.sql" ]; then
    log_info "Restoring database from backup..."
    docker compose up -d postgres
    sleep 5
    docker compose exec -T postgres psql -U mea_prod < "$BACKUP_PATH/postgres_dump.sql" || log_warn "Database restore failed"
fi

# Restart services
log_info "Restarting services..."
docker compose -f docker-compose.yml -f "deploy/compose/$ENVIRONMENT.yml" up -d

log_info "Rollback completed"
log_info "Check logs in $BACKUP_PATH/logs.log for previous state"
