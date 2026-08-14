# Motorsport Engineering Agent V3.8 — Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Motorsport Engineering Agent V3.8 multi-service runtime.

## Architecture

The deployment consists of:

- **Control Plane** (2-5 replicas): FastAPI service on port 8000
- **Worker** (2-10 replicas): Background job processor
- **MCP Server** (2-5 replicas): MCP gateway on port 7000
- **PostgreSQL**: Primary database (single replica)
- **Redis**: Cache layer (single replica)

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured with cluster access
- V3.8 component images (`mea-control-plane:3.8`, `mea-worker:3.8`, and `mea-mcp-server:3.8`) pushed to your registry
- (Optional) NGINX Ingress Controller for external access
- (Optional) cert-manager for TLS certificates

## Quick Start

### 1. Build and Push V3.8 Component Images

```bash
# Build the pinned V3.8 component images
docker build --target control_plane -t mea-control-plane:3.8 .
docker build --target worker -t mea-worker:3.8 .
docker build --target mcp_server -t mea-mcp-server:3.8 .

# Tag and push each V3.8 image for your registry
docker tag mea-control-plane:3.8 <your-registry>/mea-control-plane:3.8
docker tag mea-worker:3.8 <your-registry>/mea-worker:3.8
docker tag mea-mcp-server:3.8 <your-registry>/mea-mcp-server:3.8
docker push <your-registry>/mea-control-plane:3.8
docker push <your-registry>/mea-worker:3.8
docker push <your-registry>/mea-mcp-server:3.8
```

### 2. Update Image Reference (if using a registry)

Edit `control-plane-deployment.yaml`, `worker-deployment.yaml`, and `mcp-server-deployment.yaml`:

```yaml
# Preserve the V3.8 component tag for the deployment being edited.
image: <your-registry>/mea-control-plane:3.8
imagePullPolicy: Always  # Change from IfNotPresent if using an external registry
```

### 3. Deploy Using Kustomize

```bash
# Deploy all manifests
kubectl apply -k k8s/

# Verify deployment
kubectl get all -n mea
```

### 4. Deploy Individual Manifests (Manual)

```bash
# Create namespace and RBAC
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml

# Create ConfigMap and Secrets
kubectl apply -f k8s/app-configmap.yaml
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml

# Deploy databases
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n mea --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n mea --timeout=300s

# Deploy application services
kubectl apply -f k8s/control-plane-deployment.yaml
kubectl apply -f k8s/control-plane-service.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/mcp-server-deployment.yaml
kubectl apply -f k8s/mcp-server-service.yaml

# Apply autoscaling
kubectl apply -f k8s/hpa-control-plane.yaml
kubectl apply -f k8s/hpa-worker.yaml
kubectl apply -f k8s/hpa-mcp-server.yaml

# Apply network policies
kubectl apply -f k8s/networkpolicy.yaml

# Apply ingress (requires NGINX Ingress Controller)
kubectl apply -f k8s/ingress.yaml
```

## Post-Deployment

### Check Pod Status

```bash
# Watch deployment progress
kubectl get pods -n mea -w

# Check pod details
kubectl describe pod <pod-name> -n mea

# View logs
kubectl logs -f <pod-name> -n mea

# Logs for a specific container in a pod
kubectl logs -f <pod-name> -c <container-name> -n mea
```

### Verify Services

```bash
# List services
kubectl get svc -n mea

# Get control-plane LoadBalancer IP
kubectl get svc control-plane -n mea

# Port-forward to test locally
kubectl port-forward svc/control-plane 8000:80 -n mea
# Visit http://localhost:8000/healthz
```

### Test MCP Server

```bash
kubectl port-forward svc/mcp-server 7000:7000 -n mea
# Visit http://localhost:7000/healthz
```

## Configuration

### Environment Variables

Edit `app-configmap.yaml` to change:

```yaml
DATABASE_URL: "postgresql://mea:mea@postgres:5432/mea"
REDIS_URL: "redis://redis:6379/0"
LOG_LEVEL: "INFO"
```

### Database Credentials

Edit `postgres-secret.yaml`:

```yaml
stringData:
  POSTGRES_DB: mea
  POSTGRES_USER: mea
  POSTGRES_PASSWORD: changeme  # CHANGE THIS!
```

⚠️ **DO NOT commit secrets to Git.** Use:
- Sealed Secrets
- External Secrets Operator
- HashiCorp Vault
- Cloud-native secret management (AWS Secrets Manager, Azure Key Vault)

### Resource Limits

Adjust resource requests/limits in deployment files for your cluster:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

### Autoscaling

Control scaling thresholds in HPA manifests:

```yaml
minReplicas: 2
maxReplicas: 5
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

### Ingress Configuration

Update `ingress.yaml` with your domain:

```yaml
rules:
- host: api.example.com  # Change this
  http:
    paths:
    - path: /
      pathType: Prefix
      backend:
        service:
          name: control-plane
          port:
            number: 80
```

If using cert-manager, ensure the cluster-issuer exists:

```bash
kubectl get clusterissuer
```

## Database Management

### Connect to PostgreSQL

```bash
kubectl exec -it deployment/postgres -n mea -- psql -U mea -d mea
```

### Backup Database

```bash
kubectl exec deployment/postgres -n mea -- pg_dump -U mea mea > backup.sql
```

### Restore Database

```bash
kubectl exec -i deployment/postgres -n mea -- psql -U mea mea < backup.sql
```

### Check PVC Status

```bash
kubectl get pvc -n mea
kubectl describe pvc postgres-pvc -n mea
```

## Scaling

### Manual Scaling

```bash
# Scale control-plane to 3 replicas
kubectl scale deployment control-plane --replicas=3 -n mea

# Scale worker to 5 replicas
kubectl scale deployment worker --replicas=5 -n mea
```

### Autoscaling Status

```bash
# Check HPA status
kubectl get hpa -n mea

# Detailed HPA info
kubectl describe hpa control-plane-hpa -n mea
```

## Monitoring and Debugging

### Pod Logs

```bash
# Recent logs
kubectl logs -n mea deployment/control-plane --tail=100

# Follow logs in real-time
kubectl logs -f -n mea deployment/control-plane

# Logs from all pods with label
kubectl logs -l app=control-plane -n mea --all-containers=true
```

### Describe Pod

```bash
# Get detailed pod information
kubectl describe pod <pod-name> -n mea

# Shows events, resource usage, container status, etc.
```

### Exec into Container

```bash
# Interactive shell
kubectl exec -it <pod-name> -n mea -- /bin/sh

# Run a command
kubectl exec <pod-name> -n mea -- python -c "import sys; print(sys.version)"
```

### Check Service Connectivity

```bash
# Test DNS from a pod
kubectl exec -it <pod-name> -n mea -- nslookup postgres

# Test port connectivity
kubectl exec -it <pod-name> -n mea -- nc -zv postgres 5432
```

### Events and Troubleshooting

```bash
# Get recent cluster events
kubectl get events -n mea --sort-by='.lastTimestamp'

# Check node status
kubectl get nodes

# Check resource usage
kubectl top nodes
kubectl top pods -n mea
```

## Cleanup

### Delete All Resources

```bash
# Using kustomize
kubectl delete -k k8s/

# Or manually delete everything in the namespace
kubectl delete namespace mea
```

### Delete Specific Resources

```bash
# Delete a deployment
kubectl delete deployment control-plane -n mea

# Delete a service
kubectl delete svc control-plane -n mea

# Delete PVC (data will be lost!)
kubectl delete pvc postgres-pvc -n mea
```

## Production Considerations

### Security

- [ ] Update `postgres-secret.yaml` with strong passwords
- [ ] Use a secret management solution (Sealed Secrets, External Secrets)
- [ ] Enable RBAC for service accounts
- [ ] Apply NetworkPolicies to restrict traffic
- [ ] Use Pod Security Policies or Pod Security Standards
- [ ] Scan images for vulnerabilities

### High Availability

- [ ] Use multiple replicas for control-plane and mcp-server
- [ ] Deploy PostgreSQL with replication (consider Patroni, CloudNativePG)
- [ ] Use managed Redis (ElastiCache, Redis Cloud)
- [ ] Configure pod disruption budgets (PDB)
- [ ] Set up proper monitoring and alerting

### Backup and Disaster Recovery

- [ ] Enable automated PostgreSQL backups
- [ ] Test restore procedures regularly
- [ ] Use Velero for cluster-level backups
- [ ] Document RTO and RPO requirements

### Cost Optimization

- [ ] Set appropriate resource requests/limits
- [ ] Use cluster autoscaling
- [ ] Monitor resource utilization with Prometheus/Grafana
- [ ] Consider spot instances for non-critical workloads

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Guide](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [PostgreSQL in Kubernetes](https://www.postgresql.org/about/news/postgresql-and-kubernetes-1872/)
- [Redis on Kubernetes](https://redis.io/docs/management/scaling/kubernetes/)
