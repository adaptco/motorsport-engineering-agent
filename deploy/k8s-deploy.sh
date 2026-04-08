#!/bin/bash
set -euo pipefail

# Kubernetes deployment script for mea-root-kernel
# Usage: ./k8s-deploy.sh [cluster] [namespace]

CLUSTER="${1:-minikube}"
NAMESPACE="${2:-default}"
REGISTRY="ghcr.io/your-org/your-repo"

GREEN='\033[0;32m'
RED='\033[0;31m'
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

# Validate kubectl
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

# Set context
log_info "Using cluster: $CLUSTER, namespace: $NAMESPACE"
kubectl config use-context "$CLUSTER" || {
    log_error "Failed to switch to cluster: $CLUSTER"
    exit 1
}

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Create ConfigMap and Secrets
log_info "Applying ConfigMaps and Secrets..."
kubectl apply -f - << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: mea-config
  namespace: $NAMESPACE
data:
  ENV: "production"
  LOG_LEVEL: "warning"
  PYTHONUNBUFFERED: "1"
  PYTHONDONTWRITEBYTECODE: "1"
---
apiVersion: v1
kind: Secret
metadata:
  name: mea-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
  DATABASE_PASSWORD: changeme
  REDIS_PASSWORD: changeme
  DATABASE_URL: "postgresql://mea_prod:changeme@postgres:5432/mea_prod"
  REDIS_URL: "redis://:changeme@redis:6379/0"
EOF

# Apply RBAC
log_info "Applying RBAC..."
kubectl apply -f k8s/rbac.yaml -n "$NAMESPACE"

# Apply databases
log_info "Applying PostgreSQL and Redis..."
kubectl apply -f k8s/postgres.yaml -n "$NAMESPACE"
kubectl apply -f k8s/redis.yaml -n "$NAMESPACE"

# Wait for databases to be ready
log_info "Waiting for PostgreSQL to be ready..."
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=300s

log_info "Waiting for Redis to be ready..."
kubectl rollout status statefulset/redis -n "$NAMESPACE" --timeout=300s

# Apply applications
log_info "Applying applications..."
kubectl apply -f k8s/control-plane.yaml -n "$NAMESPACE"
kubectl apply -f k8s/worker.yaml -n "$NAMESPACE"
kubectl apply -f k8s/mcp-server.yaml -n "$NAMESPACE"

# Wait for deployments
log_info "Waiting for deployments to be ready..."
kubectl rollout status deployment/control-plane -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/mcp-server -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/worker -n "$NAMESPACE" --timeout=300s

# Show status
log_info "Deployment completed successfully!"
log_info ""
log_info "Pod status:"
kubectl get pods -n "$NAMESPACE" -o wide

log_info ""
log_info "Service endpoints:"
kubectl get svc -n "$NAMESPACE"

log_info ""
log_info "Next steps:"
log_info "  1. Port-forward control plane: kubectl port-forward -n $NAMESPACE svc/control-plane 8000:8000"
log_info "  2. Check logs: kubectl logs -n $NAMESPACE -f deployment/control-plane"
log_info "  3. Run migrations: kubectl exec -n $NAMESPACE deployment/control-plane -- alembic upgrade head"
