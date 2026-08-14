# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying mea-root-kernel to production clusters.

## Prerequisites

- Kubernetes 1.20+
- kubectl configured with cluster access
- Docker images pushed to a container registry (GitHub Container Registry, Docker Hub, etc.)
- Persistent volume provisioner (for PostgreSQL and Redis)

## Manifests

### Core Components

- **postgres.yaml**: PostgreSQL StatefulSet with persistent storage
- **redis.yaml**: Redis StatefulSet with persistent storage
- **control-plane.yaml**: Control plane Deployment with HPA
- **worker.yaml**: Worker Deployment with HPA
- **mcp-server.yaml**: MCP server Deployment with HPA
- **rbac.yaml**: ServiceAccount, RBAC, and PodDisruptionBudgets

### Features

- **High Availability**: Multiple replicas with anti-affinity rules
- **Auto-scaling**: Horizontal Pod Autoscaler for CPU/memory-based scaling
- **Health Checks**: Liveness and readiness probes for all services
- **Security**: Non-root users, read-only filesystems, security contexts
- **Resource Management**: CPU and memory requests/limits
- **Disruption Handling**: PodDisruptionBudgets for graceful degradation

## Quick Start

### 1. Prepare Environment

Update image references in manifests:

```bash
# Replace placeholder with your registry
sed -i 's|ghcr.io/your-org/your-repo|your-actual-registry|g' k8s/*.yaml
```

### 2. Update Secrets

Edit the ConfigMap and Secret in postgres.yaml:

```bash
# Edit secrets directly
kubectl edit secret mea-secrets -n default
```

Or create from environment:

```bash
kubectl create secret generic mea-secrets \
  --from-literal=DATABASE_PASSWORD=secure-password \
  --from-literal=REDIS_PASSWORD=secure-password \
  -n default
```

### 3. Deploy

Using the deployment script:

```bash
chmod +x k8s-deploy.sh
./k8s-deploy.sh minikube default
```

Or manually:

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/control-plane.yaml
kubectl apply -f k8s/worker.yaml
kubectl apply -f k8s/mcp-server.yaml
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -o wide

# Check service endpoints
kubectl get svc

# View logs
kubectl logs -f deployment/control-plane

# Port-forward for testing
kubectl port-forward svc/control-plane 8000:8000
curl http://localhost:8000/health
```

## Configuration

### ConfigMap: mea-config

Environment variables applied to all pods:

```yaml
ENV: "production"
LOG_LEVEL: "warning"
PYTHONUNBUFFERED: "1"
PYTHONDONTWRITEBYTECODE: "1"
```

Update with:

```bash
kubectl edit configmap mea-config
```

### Secret: mea-secrets

Sensitive credentials:

```yaml
DATABASE_PASSWORD: your-secure-password
REDIS_PASSWORD: your-secure-password
DATABASE_URL: postgresql://mea_prod:password@postgres:5432/mea_prod
REDIS_URL: redis://:password@redis:6379/0
```

Update with:

```bash
kubectl create secret generic mea-secrets \
  --from-literal=DATABASE_PASSWORD='secure-pass' \
  --from-literal=REDIS_PASSWORD='secure-pass' \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Scaling

### Manual Scaling

```bash
# Scale control plane to 5 replicas
kubectl scale deployment control-plane --replicas=5

# Scale worker to 10 replicas
kubectl scale deployment worker --replicas=10
```

### Horizontal Pod Autoscaler

HPAs automatically scale based on CPU and memory usage:

```bash
# View HPA status
kubectl get hpa

# Watch HPA activity
kubectl get hpa -w

# Modify HPA
kubectl edit hpa control-plane-hpa
```

Default settings:
- **control-plane**: 2-10 replicas (70% CPU, 80% memory)
- **worker**: 3-20 replicas (70% CPU, 80% memory)
- **mcp-server**: 2-8 replicas (70% CPU)

## Upgrades

### Zero-Downtime Rollout

Update image and perform rolling update:

```bash
# Update image
kubectl set image deployment/control-plane \
  control-plane=your-registry/control-plane:v0.3.8

# Monitor rollout
kubectl rollout status deployment/control-plane

# Rollback if needed
kubectl rollout undo deployment/control-plane
```

### Database Migrations

Run migrations before deployment:

```bash
# Via kubectl run
kubectl run migrate \
  --image=your-registry/control-plane:latest \
  --restart=Never \
  -it \
  -- alembic upgrade head

# Or via exec
kubectl exec -it deployment/control-plane -- alembic upgrade head
```

## Monitoring & Troubleshooting

### Logs

```bash
# View pod logs
kubectl logs deployment/control-plane -f

# View logs from previous crashed container
kubectl logs deployment/control-plane --previous

# View logs from all pods in a deployment
kubectl logs -f deployment/control-plane --all-containers=true
```

### Debugging

```bash
# Describe pod
kubectl describe pod <pod-name>

# Get pod details
kubectl get pod <pod-name> -o yaml

# Enter pod shell
kubectl exec -it <pod-name> -- /bin/sh

# Check events
kubectl get events --sort-by='.lastTimestamp'
```

### Health & Status

```bash
# Pod status
kubectl get pods

# Deployment status
kubectl get deployments

# StatefulSet status
kubectl get statefulsets

# Service endpoints
kubectl get endpoints

# PVC status
kubectl get pvc
```

### Performance

```bash
# Resource usage
kubectl top pods
kubectl top nodes

# Monitor pod metrics
kubectl describe node <node-name>
```

## Network & Ingress

### Port Forwarding (Development)

```bash
# Forward control plane port
kubectl port-forward svc/control-plane 8000:8000

# Forward MCP server port
kubectl port-forward svc/mcp-server 7000:7000

# Forward PostgreSQL (for admin tools)
kubectl port-forward svc/postgres 5432:5432
```

### Ingress (Production)

Create an Ingress for external access:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mea-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: mea-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: control-plane
            port:
              number: 8000
```

Apply with:

```bash
kubectl apply -f ingress.yaml
```

## Backup & Recovery

### PostgreSQL Backup

```bash
# Create backup
kubectl exec -it statefulset/postgres -- \
  pg_dump -U mea_prod mea_prod > backup.sql

# Restore backup
kubectl exec -i statefulset/postgres -- \
  psql -U mea_prod mea_prod < backup.sql
```

### Redis Backup

```bash
# Create backup
kubectl exec statefulset/redis -- redis-cli BGSAVE
kubectl cp default/redis-0:/data/dump.rdb ./redis-dump.rdb

# Restore backup
kubectl cp redis-dump.rdb default/redis-0:/data/dump.rdb
kubectl exec statefulset/redis -- redis-cli BGREWRITEAOF
```

## Security

### Network Policies

Restrict traffic between pods:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mea-network-policy
spec:
  podSelector:
    matchLabels:
      app: control-plane
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: default
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: default
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
```

### Pod Security

- All containers run as non-root user (5678)
- Read-only root filesystem
- No privileged escalation
- Capabilities dropped
- Security context enforced

### Secrets Management

For production, use a secrets manager:

- **Sealed Secrets**: Encrypt secrets in git
- **Vault**: Hashicorp Vault integration
- **External Secrets**: Sync with external secret stores

## Disaster Recovery

### Backup Strategy

```bash
# Regular PostgreSQL backups (cron job)
0 2 * * * kubectl exec statefulset/postgres -- pg_dump -U mea_prod mea_prod | gzip > backups/pg-$(date +%Y%m%d).sql.gz

# Store backups off-cluster (S3, GCS, etc.)
```

### Restore Procedure

1. Scale down applications:
   ```bash
   kubectl scale deployment control-plane --replicas=0
   kubectl scale deployment worker --replicas=0
   kubectl scale deployment mcp-server --replicas=0
   ```

2. Restore database:
   ```bash
   kubectl exec statefulset/postgres -- psql -U mea_prod mea_prod < backup.sql
   ```

3. Scale up applications:
   ```bash
   kubectl scale deployment control-plane --replicas=2
   kubectl scale deployment worker --replicas=3
   kubectl scale deployment mcp-server --replicas=2
   ```

## Example Workflows

### Complete Deployment

```bash
# Prepare
kubectl create namespace mea
kubectl config set-context --current --namespace=mea

# Create secrets
kubectl create secret generic mea-secrets \
  --from-literal=DATABASE_PASSWORD='prod-secure-pass' \
  --from-literal=REDIS_PASSWORD='prod-secure-pass'

# Deploy
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s

# Deploy applications
kubectl apply -f k8s/control-plane.yaml
kubectl apply -f k8s/worker.yaml
kubectl apply -f k8s/mcp-server.yaml

# Wait for readiness
kubectl rollout status deployment/control-plane --timeout=300s
kubectl rollout status deployment/worker --timeout=300s
kubectl rollout status deployment/mcp-server --timeout=300s

# Run migrations
kubectl exec -it deployment/control-plane -- alembic upgrade head

# Verify
kubectl get all
kubectl logs deployment/control-plane
```

### Update & Rollback

```bash
# Update image
kubectl set image deployment/control-plane \
  control-plane=your-registry/control-plane:v0.3.8

# Monitor
kubectl rollout status deployment/control-plane

# If needed, rollback
kubectl rollout undo deployment/control-plane
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
