#!/bin/bash
set -euo pipefail

# V3.8 Deployment Verification Script
# Validates runtime contracts, event order, and deployment topology

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    PASSED=$((PASSED + 1))
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    FAILED=$((FAILED + 1))
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================
# 1. Version Alignment
# ============================================================
log_header "Version Validation"

if [ ! -f "VERSION.json" ]; then
    check_fail "VERSION.json not found"
else
    kernel_version=$(python -c "import json; print(json.load(open('VERSION.json'))['kernel_version'])" 2>/dev/null || echo "")
    package_version=$(python -c "import json; print(json.load(open('VERSION.json'))['package_version'])" 2>/dev/null || echo "")
    
    if [[ "$kernel_version" == "3.8" ]]; then
        check_pass "Kernel version is 3.8"
    else
        check_fail "Kernel version is $kernel_version (expected 3.8)"
    fi
    
    if [[ "$package_version" == "0.3.8" ]]; then
        check_pass "Package version is 0.3.8"
    else
        check_fail "Package version is $package_version (expected 0.3.8)"
    fi
fi

# ============================================================
# 2. Runtime Contract Bundle
# ============================================================
log_header "Runtime Contract Validation"

if [ -f "contracts/runtime/agent_runtime_contract_bundle.schema.json" ]; then
    check_pass "Runtime contract bundle found"
    
    # Validate JSON
    if python -c "import json; json.load(open('contracts/runtime/agent_runtime_contract_bundle.schema.json'))" 2>/dev/null; then
        check_pass "Runtime contract bundle is valid JSON"
    else
        check_fail "Runtime contract bundle has invalid JSON"
    fi
    
    # Check for required event types
    bundle=$(cat contracts/runtime/agent_runtime_contract_bundle.schema.json)
    
    required_events=(
        "request.received"
        "run.created"
        "workflow.policy.screened"
        "plan.proposed"
        "step.dispatched"
        "tool.requested"
        "tool.executed"
        "state.transitioned"
        "checkpoint.persisted"
        "run.completed"
        "run.failed"
    )
    
    for event in "${required_events[@]}"; do
        if echo "$bundle" | grep -q "\"$event\""; then
            check_pass "Event type '$event' defined"
        else
            check_warn "Event type '$event' not found in bundle"
        fi
    done
else
    check_warn "Runtime contract bundle not found at contracts/runtime/"
fi

# ============================================================
# 3. Aero Simulation Contracts (Optional)
# ============================================================
log_header "Aero Simulation Contracts (Optional)"

if [ -f "contracts/aero/aero_simulation_state.schema.json" ]; then
    check_pass "Aero simulation contract found"
    
    if python -c "import json; json.load(open('contracts/aero/aero_simulation_state.schema.json'))" 2>/dev/null; then
        check_pass "Aero simulation contract is valid JSON"
    else
        check_fail "Aero simulation contract has invalid JSON"
    fi
else
    check_warn "Aero simulation contract not found (optional for v3.8.0)"
fi

# ============================================================
# 4. Dockerfile Structure
# ============================================================
log_header "Dockerfile Validation"

if [ -f "Dockerfile" ]; then
    check_pass "Root Dockerfile exists"
    
    # Check for multi-stage targets
    targets=("control_plane" "worker" "mcp_server")
    for target in "${targets[@]}"; do
        if grep -q "FROM .* as $target" Dockerfile; then
            check_pass "Dockerfile target '$target' found"
        else
            check_fail "Dockerfile target '$target' not found"
        fi
    done
else
    check_fail "Root Dockerfile not found"
fi

if [ -f "deploy/containers/mea-v3.8/Dockerfile" ]; then
    check_pass "v3.8 Dockerfile found"
    
    # Check for v3.8 base
    if grep -q "as v3.8-base" deploy/containers/mea-v3.8/Dockerfile; then
        check_pass "v3.8 base image defined"
    else
        check_fail "v3.8 base image not defined"
    fi
else
    check_warn "v3.8 Dockerfile not found (optional for initial deployment)"
fi

# ============================================================
# 5. Docker Compose Topology
# ============================================================
log_header "Docker Compose Topology"

compose_available=false
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    compose_available=true
else
    check_warn "Docker Compose is unavailable; runtime configuration checks are skipped locally"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
    
    # Validate compose when the local runtime is available.
    if [ "$compose_available" = true ]; then
        if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
            check_pass "docker-compose.yml is valid"
        else
            check_fail "docker-compose.yml validation failed"
        fi
    else
        check_warn "docker-compose.yml runtime validation skipped"
    fi
    
    # Check services
    services=("postgres" "redis" "control_plane" "worker" "mcp_server")
    for service in "${services[@]}"; do
        if grep -q "^  $service:" docker-compose.yml; then
            check_pass "Service '$service' defined"
        else
            check_fail "Service '$service' not defined"
        fi
    done
else
    check_fail "docker-compose.yml not found"
fi

if [ -f "deploy/compose/docker-compose.v3.8.yml" ]; then
    check_pass "v3.8 compose overlay found"
    
    if [ "$compose_available" = true ]; then
        if docker compose -f docker-compose.yml -f deploy/compose/docker-compose.v3.8.yml config > /dev/null 2>&1; then
            check_pass "v3.8 compose overlay is valid"
        else
            check_fail "v3.8 compose overlay validation failed"
        fi
    else
        check_warn "v3.8 compose overlay runtime validation skipped"
    fi
else
    check_warn "v3.8 compose overlay not found (optional)"
fi

# ============================================================
# 6. Environment Files
# ============================================================
log_header "Environment Configuration"

envs=("staging" "production")
for env in "${envs[@]}"; do
    if [ -f "deploy/compose/$env.yml" ]; then
        check_pass "Environment override for '$env' found"
        
        if [ "$compose_available" = true ]; then
            if docker compose -f docker-compose.yml -f "deploy/compose/$env.yml" config > /dev/null 2>&1; then
                check_pass "Environment override for '$env' is valid"
            else
                check_fail "Environment override for '$env' validation failed"
            fi
        else
            check_warn "Environment override for '$env' runtime validation skipped"
        fi
    else
        check_fail "Environment override for '$env' not found"
    fi
done

# ============================================================
# 7. Deployment Scripts
# ============================================================
log_header "Deployment Scripts"

scripts=("deploy.sh" "setup.sh" "backup.sh" "rollback.sh")
for script in "${scripts[@]}"; do
    if [ -f "deploy/$script" ]; then
        check_pass "Deployment script '$script' found"
    else
        check_warn "Deployment script '$script' not found"
    fi
done

# ============================================================
# 8. Documentation
# ============================================================
log_header "Documentation"

docs=("README.md" "DEPLOYMENT.md" "K8S.md" "RUNBOOK.md")
for doc in "${docs[@]}"; do
    if [ -f "deploy/$doc" ]; then
        check_pass "Documentation '$doc' found"
    else
        check_warn "Documentation '$doc' not found"
    fi
done

# ============================================================
# 9. CI/CD Workflows
# ============================================================
log_header "CI/CD Workflows"

if [ -f ".github/workflows/deploy.yml" ]; then
    check_pass "Deploy workflow found"
    
    if grep -q "validate-version" .github/workflows/deploy.yml; then
        check_pass "Version validation in deploy workflow"
    else
        check_warn "Version validation not found in deploy workflow"
    fi
    
    if grep -q "runtime.contract" .github/workflows/deploy.yml; then
        check_pass "Runtime contract validation in deploy workflow"
    else
        check_warn "Runtime contract validation not in deploy workflow"
    fi
else
    check_fail "Deploy workflow not found"
fi

# ============================================================
# 10. Running Services (if available)
# ============================================================
log_header "Running Services Health"

if command -v docker &> /dev/null; then
    # Check if docker daemon is running
    if docker ps > /dev/null 2>&1; then
        services_count=$(docker ps -a --filter "status=running" -q | wc -l)
        if [ $services_count -gt 0 ]; then
            check_pass "Docker daemon is running with $services_count containers"
            
            # Check specific services if running
            if docker ps --filter "name=mea-control-plane" | grep -q "Up"; then
                check_pass "Control plane is running"
                
                # Check health endpoint
                if docker exec mea-control-plane curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
                    check_pass "Control plane /healthz endpoint is healthy"
                else
                    check_warn "Control plane /healthz endpoint check failed"
                fi
            else
                check_warn "Control plane not running (expected if not deployed)"
            fi
        else
            check_warn "No running Docker containers"
        fi
    else
        check_warn "Docker daemon not running"
    fi
fi

# ============================================================
# Summary
# ============================================================
log_header "Verification Summary"

echo ""
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}  $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed. v3.8 deployment ready.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Checks passed with warnings. Review above and proceed with caution.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Checks failed. Review errors above and fix before deploying.${NC}"
    exit 1
fi
