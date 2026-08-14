# MEA v3.8 Container Image
# Runtime contract bundle validated, runtime events enforceable
# Builds control-plane, worker, mcp-server with unified v3.8 base

FROM python:3.11-slim as v3.8-base

LABEL version="3.8" \
      maintainer="adaptco" \
      description="MEA v3.8: Runtime contracts + checkpoint resumption"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEA_VERSION=3.8 \
    MEA_KERNEL_VERSION=3.8

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --uid 5678 --disabled-password --gecos "" appuser

# ============================================================
# v3.8 Builder: Install dependencies + validate contracts
# ============================================================
FROM v3.8-base as v3.8-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml uv.lock ./
COPY contracts/runtime/ ./contracts/runtime/

# Validate runtime contract bundle
RUN python -c "import json; json.load(open('contracts/runtime/agent_runtime_contract_bundle.schema.json')); print('✓ Runtime contract bundle valid')" || exit 1

# Create virtual environment
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel uv && \
    uv sync --frozen --no-install-project --python /opt/venv/bin/python --active

# ============================================================
# v3.8 Control Plane
# ============================================================
FROM v3.8-base as v3.8-control-plane

COPY --from=v3.8-builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY control_plane/ ./control_plane/
COPY shared/ ./shared/
COPY contracts/ ./contracts/
COPY pyproject.toml ./
COPY VERSION.json ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "control_plane.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
# v3.8 Worker
# ============================================================
FROM v3.8-base as v3.8-worker

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=v3.8-builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY control_plane/ ./control_plane/
COPY worker/ ./worker/
COPY shared/ ./shared/
COPY contracts/ ./contracts/
COPY pyproject.toml ./
COPY VERSION.json ./

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "worker.backend_worker"]

# ============================================================
# v3.8 MCP Server
# ============================================================
FROM v3.8-base as v3.8-mcp-server

COPY --from=v3.8-builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY mcp_server/ ./mcp_server/
COPY mcp_tools/ ./mcp_tools/
COPY shared/ ./shared/
COPY contracts/ ./contracts/
COPY pyproject.toml ./
COPY VERSION.json ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 7000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7000/healthz || exit 1

CMD ["uvicorn", "mcp_server.app:app", "--host", "0.0.0.0", "--port", "7000"]

# ============================================================
# Default: control-plane
# ============================================================
FROM v3.8-control-plane as latest
