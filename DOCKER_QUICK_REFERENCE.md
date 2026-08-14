# Docker Quick Reference

## Daily Commands

### Start all services (production)
```bash
docker compose up -d
```

### Start with live code reload (development)
```bash
docker compose up
# Uses docker-compose.override.yml automatically
```

### View logs
```bash
docker compose logs -f control_plane
docker compose logs -f worker
docker compose logs -f mcp_server
```

### Stop all services
```bash
docker compose down
```

### Clean up everything (including volumes)
```bash
docker compose down -v
```

---

## Building

### Build all services
```bash
docker compose build
```

### Build specific service
```bash
docker compose build control_plane
```

### Build and run in one step
```bash
docker compose up --build
```

---

## Testing

### Execute command in running container
```bash
docker compose exec control_plane python -m pytest tests/
```

### Run interactive shell
```bash
docker compose exec control_plane /bin/bash
```

### Check service status
```bash
docker compose ps
```

### View service configuration
```bash
docker compose config
```

---

## Debugging

### Check container logs
```bash
docker compose logs control_plane
```

### Follow logs in real-time
```bash
docker compose logs -f control_plane --tail 50
```

### Inspect container network
```bash
docker inspect mea-control-plane
```

### Check service health
```bash
docker compose ps  # Shows health status
docker inspect mea-postgres  # Full details
```

---

## Docker File Structure

```
Dockerfile                    # Single unified Dockerfile (4 targets)
docker-compose.yml            # Production config
docker-compose.override.yml   # Development overrides (auto-merged)
.dockerignore                 # Build context exclusions
```

### Targets in Dockerfile
- `control_plane` - FastAPI server (port 8000)
- `worker` - Background job processor
- `mcp_server` - FastAPI MCP server (port 7000)
- `latest` - Alias to control_plane

---

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| control_plane | 8000 | HTTP API |
| mcp_server | 7000 | MCP HTTP API |
| postgres | 5432 | Database |
| redis | 6379 | Cache/Queue |

---

## Environment Variables

Create `.env` file:
```bash
cp .env.example .env
# Edit as needed
```

Services load from `.env` via `env_file: .env` in docker-compose.yml

---

## Common Issues & Solutions

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # External:Internal
```

### Container won't start
```bash
docker compose logs control_plane  # Check error
docker compose exec control_plane /bin/bash  # Debug
```

### Health check failing
```bash
docker compose ps  # Check status
docker logs mea-control-plane  # View logs
```

### Need fresh database
```bash
docker compose down -v  # Remove volumes
docker compose up -d    # Restart (will reinitialize)
```

---

## Development Workflow

### 1. Start services with hot reload
```bash
docker compose up
```

### 2. Edit code (e.g., control_plane/app.py)
```bash
# Changes sync automatically via file watch
```

### 3. View changes in logs
```bash
docker compose logs -f control_plane
```

### 4. Run tests
```bash
docker compose exec control_plane python -m pytest tests/
```

### 5. Stop when done
```bash
Ctrl+C
docker compose down
```

---

## Production Deployment

### 1. Build images (one-time)
```bash
docker compose build
```

### 2. Start services
```bash
docker compose up -d
```

### 3. Monitor health
```bash
docker compose ps
docker compose logs -f control_plane
```

### 4. Update on new code
```bash
git pull
docker compose build
docker compose up -d
```

---

## Image Tags

Standardized naming:
- `mea-control-plane:3.8` - Production control plane
- `mea-worker:3.8` - Production worker
- `mea-mcp-server:3.8` - Production MCP server

Built with:
```bash
docker build -t mea-control-plane:3.8 --target control_plane .
```

---

## Advanced

### View multi-stage build intermediate layers
```bash
docker build -t intermediate --target builder .
docker run -it intermediate /bin/bash
```

### Force rebuild (no cache)
```bash
docker compose build --no-cache
```

### Prune unused images/containers
```bash
docker system prune -a
```

### Export image for transfer
```bash
docker save mea-control-plane:3.8 | gzip > control-plane.tar.gz
docker load < control-plane.tar.gz
```

---

## For More Info

- Dockerfile: `cat Dockerfile`
- Compose: `cat docker-compose.yml`
- Dev overrides: `cat docker-compose.override.yml`
- Report: `cat DOCKER_OPTIMIZATION_REPORT.md`
