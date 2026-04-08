#!/bin/bash
set -euo pipefail

# Development environment setup
# Usage: ./dev-setup.sh

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_info "Setting up development environment..."

# Create necessary directories
mkdir -p logs/control_plane logs/worker logs/mcp_server

# Create .env.dev if it doesn't exist
if [ ! -f ".env.dev" ]; then
    log_info "Creating .env.dev..."
    cat > .env.dev << 'EOF'
# Development environment variables
ENV=development
LOG_LEVEL=debug
DEBUG=true

# Database
POSTGRES_DB=mea_dev
POSTGRES_USER=mea
POSTGRES_PASSWORD=mea

# Redis
REDIS_PASSWORD=

# API Configuration
WORKERS=2
WORKER_CONCURRENCY=4
DATABASE_POOL_SIZE=5
EOF
    log_warn "Created .env.dev - update with your values"
fi

# Create .env.staging if it doesn't exist
if [ ! -f ".env.staging" ]; then
    log_info "Creating .env.staging..."
    cat > .env.staging << 'EOF'
# Staging environment variables
ENV=staging
LOG_LEVEL=info

# Database - Update these with actual credentials
POSTGRES_DB=mea_staging
POSTGRES_USER=mea
POSTGRES_PASSWORD=changeme

# Redis
REDIS_PASSWORD=changeme

# API Configuration
WORKERS=4
WORKER_CONCURRENCY=8
DATABASE_POOL_SIZE=20
EOF
    log_warn "Created .env.staging - update with your actual staging credentials"
fi

# Create .env.production if it doesn't exist
if [ ! -f ".env.production" ]; then
    log_info "Creating .env.production..."
    cat > .env.production << 'EOF'
# Production environment variables
ENV=production
LOG_LEVEL=warning

# Database - Use secure credentials in production
POSTGRES_DB=mea_prod
POSTGRES_USER=mea_prod
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION

# Redis
REDIS_PASSWORD=CHANGE_ME_IN_PRODUCTION

# API Configuration
WORKERS=8
WORKER_CONCURRENCY=16
DATABASE_POOL_SIZE=50
EOF
    log_warn "Created .env.production - MUST be updated with secure production credentials"
fi

# Make scripts executable
chmod +x deploy/deploy.sh deploy/rollback.sh deploy/backup.sh

log_info "✓ Development environment setup completed"
log_info ""
log_info "Next steps:"
log_info "  1. Update .env.dev, .env.staging, and .env.production with your credentials"
log_info "  2. Run: docker compose up"
log_info "  3. Run migrations: docker compose exec control_plane alembic upgrade head"
log_info "  4. Check health: curl http://localhost:8000/healthz"
