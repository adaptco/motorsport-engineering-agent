# Operational Runbook

Common operations and troubleshooting procedures for the mea-root-kernel deployment.

## Table of Contents

1. [Deployment Operations](#deployment-operations)
2. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
3. [Emergency Procedures](#emergency-procedures)
4. [Common Issues](#common-issues)
5. [Performance Optimization](#performance-optimization)

## Deployment Operations

### Deploying a New Version

#### Docker Compose

```bash
# Staging (from main branch)
cd deploy
./deploy.sh staging

# Production (from version tag)
./deploy.sh production v0.3.5.1
```

#### Kubernetes

```bash
# Update image
kubectl set image deployment/control-plane \
  control-plane=ghcr.io/your-org/your-repo/control-plane:v0.3.5.1

# Monitor rollout
kubectl rollout status deployment/control-plane -w

# Rollback if needed
kubectl rollout undo deployment/control-plane
```

### Database Migrations

#### Before Deployment

```bash
# Docker Compose
docker compose exec control_plane alembic upgrade head

# Kubernetes
kubectl exec -it deployment/control-plane -- alembic upgrade head
```

#### Checking Migration Status

```bash
# Docker Compose
docker compose exec control_plane alembic current

# Kubernetes
kubectl exec deployment/control-plane -- alembic current
```

#### Rolling Back Migrations

```bash
# Docker Compose
docker compose exec control_plane alembic downgrade -1

# Kubernetes
kubectl exec deployment/control-plane -- alembic downgrade -1
```

### Scaling Services

#### Docker Compose

```bash
# Scale worker replicas (if using profiles)
docker compose up -d --scale worker=5
```

#### Kubernetes

```bash
# Manual scaling
kubectl scale deployment worker --replicas=10

# HPA automatically scales based on metrics
kubectl get hpa
kubectl describe hpa worker-hpa
```

## Monitoring & Troubleshooting

### Health Checks

#### Service Health

```bash
# Docker Compose
curl http://localhost:8000/health          # control-plane
curl http://localhost:7000/health          # mcp-server

# Kubernetes
kubectl port-forward svc/control-plane 8000:8000
curl http://localhost:8000/health

kubectl port-forward svc/mcp-server 7000:7000
curl http://localhost:7000/health
```

#### Service Status

```bash
# Docker Compose
docker compose ps

# Kubernetes
kubectl get pods -o wide
kubectl get deployments
kubectl get statefulsets
```

### Viewing Logs

#### Docker Compose

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f control_plane
docker compose logs -f worker
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail 100 control_plane

# Specific timeframe
docker compose logs --since 2024-01-15 control_plane
```

#### Kubernetes

```bash
# Current logs
kubectl logs deployment/control-plane
kubectl logs -f deployment/control-plane

# Previous pod (crashed)
kubectl logs deployment/control-plane --previous

# All containers
kubectl logs deployment/control-plane --all-containers=true

# Specific container
kubectl logs deployment/control-plane -c control-plane

# Follow with timestamps
kubectl logs -f deployment/control-plane --timestamps=true
```

### Debugging Pods

#### Kubernetes

```bash
# Describe pod for events
kubectl describe pod <pod-name>

# Shell into pod
kubectl exec -it <pod-name> -- /bin/sh

# Check resource usage
kubectl top pods
kubectl top pod <pod-name>

# Get pod configuration
kubectl get pod <pod-name> -o yaml

# Check recent events
kubectl get events --sort-by='.lastTimestamp'
```

### Database Health

#### PostgreSQL

```bash
# Docker Compose
docker compose exec postgres pg_isready -U mea_prod

# Kubernetes
kubectl exec statefulset/postgres -- pg_isready -U mea_prod

# Connect to database
docker compose exec postgres psql -U mea_prod -d mea_prod
kubectl exec -it statefulset/postgres -- psql -U mea_prod -d mea_prod

# Check active connections
docker compose exec postgres psql -U mea_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

#### Redis

```bash
# Docker Compose
docker compose exec redis redis-cli ping

# Kubernetes
kubectl exec statefulset/redis -- redis-cli ping

# Check memory usage
docker compose exec redis redis-cli info memory
kubectl exec statefulset/redis -- redis-cli info memory

# Monitor keys
docker compose exec redis redis-cli MONITOR
```

## Emergency Procedures

### Service Down - Immediate Response

1. **Check Status**
   ```bash
   docker compose ps  # or kubectl get pods
   ```

2. **Review Logs**
   ```bash
   docker compose logs <service>  # or kubectl logs deployment/<service>
   ```

3. **Check Resources**
   ```bash
   docker stats  # or kubectl top pods
   ```

4. **Restart if Needed**
   ```bash
   # Docker Compose
   docker compose restart <service>
   
   # Kubernetes - pod restarts automatically
   # If not, delete pod to force recreation
   kubectl delete pod <pod-name>
   ```

### Database Connectivity Issues

1. **Check Database Status**
   ```bash
   docker compose exec postgres pg_isready -U mea_prod
   kubectl exec statefulset/postgres -- pg_isready -U mea_prod
   ```

2. **Check Connection String**
   ```bash
   docker compose exec control_plane printenv | grep DATABASE
   kubectl exec deployment/control-plane -- printenv | grep DATABASE
   ```

3. **Check Network Connectivity**
   ```bash
   # Docker Compose
   docker compose exec control_plane ping postgres
   
   # Kubernetes
   kubectl exec deployment/control-plane -- ping postgres
   ```

4. **Increase Connection Timeout**
   ```bash
   # Docker Compose - edit .env file
   docker compose restart control_plane
   
   # Kubernetes
   kubectl set env deployment/control-plane DATABASE_TIMEOUT=30
   ```

### High CPU/Memory Usage

1. **Identify Problem Service**
   ```bash
   docker stats  # Docker Compose
   kubectl top pods  # Kubernetes
   ```

2. **Check Logs for Errors**
   ```bash
   docker compose logs <service>
   kubectl logs deployment/<service>
   ```

3. **Scale Horizontally**
   ```bash
   # Kubernetes
   kubectl scale deployment worker --replicas=10
   ```

4. **Adjust Resource Limits**
   ```bash
   # Kubernetes
   kubectl set resources deployment/control-plane \
     --limits=cpu=4,memory=4Gi \
     --requests=cpu=1,memory=1Gi
   ```

### Disk Space Issues

#### Docker Compose

```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a
docker image prune -a
docker container prune
docker volume prune

# Remove specific image/container
docker rmi <image>
docker rm <container>
```

#### Kubernetes

```bash
# Check PVC usage
kubectl get pvc
kubectl describe pvc <pvc-name>

# Increase storage
kubectl patch pvc <pvc-name> -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

## Common Issues

### Container Won't Start

**Symptom**: Container exits immediately or keeps restarting

**Diagnosis**:
```bash
docker compose logs <service>
kubectl logs deployment/<service>
kubectl describe pod <pod-name>
```

**Common Causes & Solutions**:

1. **Image Pull Error**
   - Verify image name and tag
   - Check registry credentials
   - Ensure image exists

   ```bash
   # Docker Compose
   docker pull <image:tag>
   
   # Kubernetes
   kubectl describe pod <pod-name>  # Look for ImagePullBackOff
   ```

2. **Missing Environment Variables**
   - Check .env file or ConfigMap/Secret
   - Verify variable names match code

   ```bash
   # Docker Compose
   docker compose config | grep <variable>
   
   # Kubernetes
   kubectl exec deployment/<service> -- printenv | grep <variable>
   ```

3. **Port Already in Use**
   - Check what's using the port
   - Change port mapping

   ```bash
   # Docker
   lsof -i :8000
   
   # Kubernetes - usually not an issue, pods isolated by default
   ```

### Database Connection Timeout

**Symptom**: Timeout waiting for database connection

**Diagnosis**:
```bash
docker compose exec <service> curl -v postgresql://postgres:5432
kubectl exec deployment/<service> -- curl -v postgresql://postgres:5432
```

**Solutions**:

1. **Database Not Ready**
   ```bash
   docker compose exec postgres pg_isready -U mea_prod
   kubectl exec statefulset/postgres -- pg_isready -U mea_prod
   ```

2. **Network Isolation**
   - Docker: Check docker network
   - Kubernetes: Check NetworkPolicy

3. **Connection Pool Exhausted**
   - Increase DATABASE_POOL_SIZE
   - Reduce number of replicas temporarily

### High Latency / Slow Responses

**Diagnosis**:
```bash
# Check database performance
docker compose exec postgres psql -U mea_prod -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Redis memory
docker compose exec redis redis-cli info memory

# Check network latency
docker compose exec <service> ping postgres
```

**Solutions**:

1. **Add Database Indexes**
   - Review slow queries
   - Add indexes to frequently queried columns

2. **Increase Cache Size**
   - Increase Redis memory limit
   - Clear expired cache

3. **Scale Workers**
   ```bash
   kubectl scale deployment worker --replicas=10
   ```

### Memory Leak

**Symptom**: Memory usage gradually increases

**Diagnosis**:
```bash
# Monitor memory over time
docker stats --no-stream <service>

# Check for circular references in logs
docker compose logs <service> | grep -i "memory\|leak"
```

**Solutions**:

1. **Restart Service**
   ```bash
   docker compose restart <service>
   kubectl delete pod <pod-name>  # Forces restart
   ```

2. **Update Limit and Monitor**
   ```bash
   kubectl set resources deployment/<service> \
     --limits=memory=2Gi
   ```

3. **Profile Application**
   - Use Python memory profilers
   - Identify problematic code
   - Apply fixes in new release

## Performance Optimization

### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Add indexes
CREATE INDEX idx_name ON table(column);
CREATE UNIQUE INDEX idx_unique ON table(unique_column);

-- Analyze table
ANALYZE table_name;

-- Vacuum database
VACUUM ANALYZE;
```

### Connection Pooling

```yaml
# Kubernetes ConfigMap
DATABASE_POOL_SIZE: "50"        # Max connections
DATABASE_POOL_TIMEOUT: "30"     # Timeout in seconds
DATABASE_POOL_RECYCLE: "3600"   # Recycle after 1 hour
```

### Caching Strategy

```python
# Use Redis for frequently accessed data
redis.set("key", value, ex=3600)  # Expire after 1 hour
redis.get("key")
```

### Worker Configuration

```yaml
# Optimize for CPU-bound tasks
WORKER_CONCURRENCY: "4"  # For 4 CPU cores

# Optimize for I/O-bound tasks
WORKER_CONCURRENCY: "16"  # Higher concurrency
```

### Kubernetes HPA Tuning

```bash
# Adjust HPA metrics
kubectl patch hpa worker-hpa --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/metrics/0/resource/target/averageUtilization",
    "value": 60
  }
]'

# View current HPA config
kubectl get hpa -o yaml
```

### Resource Requests/Limits

Ensure requests match actual usage:

```bash
# Monitor usage
kubectl top pods

# Adjust if needed
kubectl set resources deployment/<service> \
  --requests=cpu=500m,memory=512Mi \
  --limits=cpu=2,memory=2Gi
```

## Preventive Maintenance

### Regular Backups

```bash
# Daily backups (add to cron)
0 2 * * * cd /opt/mea && ./deploy/backup.sh production

# Weekly full system backup
0 3 * * 0 cd /opt/mea && ./deploy/backup.sh production && rsync -av backups/ remote-backup-server:backups/
```

### Log Rotation

```bash
# Docker Compose
docker system prune --filter "until=72h"

# Kubernetes
kubectl delete pods --field-selector=status.phase=Failed -A
kubectl delete pods --field-selector=status.phase=Succeeded -A
```

### Update Images

```bash
# Pull latest images
docker compose pull
docker image prune -a

# Kubernetes
kubectl set image deployment/* $(kubectl get deployment -o jsonpath='{.items[*].metadata.name}')=$(kubectl get deployment -o jsonpath='{.items[*].spec.template.spec.containers[0].image}'):latest
```

### Monitor Metrics

Keep an eye on:
- CPU usage
- Memory usage
- Disk space
- Network I/O
- Database connections
- Redis memory
- Request latency
- Error rates

## Related Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
- [K8S.md](K8S.md) - Kubernetes operations
- [README.md](README.md) - Quick start and overview
