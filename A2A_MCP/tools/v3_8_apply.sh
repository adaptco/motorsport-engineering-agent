#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/A2A_MCP}"

mkdir -p "$ROOT/docs/v3.8"
mkdir -p "$ROOT/infra/env"
mkdir -p "$ROOT/packages/cfd-contracts/src"
mkdir -p "$ROOT/packages/cfd-multimodal-agent/apps/api/src/cfd_api"
mkdir -p "$ROOT/packages/cfd-multimodal-agent/apps/api/tests"
mkdir -p "$ROOT/packages/cfd-multimodal-agent/apps/web/src"
mkdir -p "$ROOT/tools"

echo "Create files from the V3.8 canvas document in these paths:"
echo "  $ROOT/packages/cfd-contracts"
echo "  $ROOT/packages/cfd-multimodal-agent"
echo "  $ROOT/docs/v3.8"
echo "  $ROOT/infra/env"
echo "Then run:"
echo "  make cfd-api-install"
echo "  make cfd-api-test"
echo "  make cfd-web-install"
echo "  make cfd-web-build"
echo "  make cfd-stack-up"
