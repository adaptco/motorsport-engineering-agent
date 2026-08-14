# Multi-target unified Dockerfile for mea-root-kernel
# Builds: control_plane, worker, mcp_server
# Usage:
#   docker build -t mea-control-plane --target control_plane .
#   docker build -t mea-worker --target worker .
#   docker build -t mea-mcp-server --target mcp_server .
#   docker build -t mea-app .  (default: control_plane)

# ============================================================
# STAGE 1: Base - Common Python environment
# ============================================================
FROM python:3.11-slim-bookworm as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install common system dependencies in a single atomic apt step
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (same UID across all targets for consistency)
RUN adduser --uid 5678 --disabled-password --gecos "" appuser

# ============================================================
# STAGE 2: Builder - Install all dependencies
# ============================================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Create virtual environment and install all dependencies from lockfile
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel uv && \
    uv sync --frozen --no-install-project --python /opt/venv/bin/python --active

# ============================================================
# STAGE 3: Control Plane
# ============================================================
FROM base as control_plane

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY control_plane/ ./control_plane/
COPY ingest/ ./ingest/
COPY shared/ ./shared/
COPY pyproject.toml ./
COPY VERSION.json ./
COPY LICENSES/ ./LICENSES/
COPY DEPENDENCIES.md ./DEPENDENCIES.md
COPY frontend/ ./frontend/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "control_plane.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
# STAGE 4: Worker
# ============================================================
FROM base as worker

# Worker needs git for potential runtime operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY control_plane/ ./control_plane/
COPY ingest/ ./ingest/
COPY worker/ ./worker/
COPY shared/ ./shared/
COPY pyproject.toml ./
COPY VERSION.json ./
COPY LICENSES/ ./LICENSES/
COPY DEPENDENCIES.md ./DEPENDENCIES.md

RUN chown -R appuser:appuser /app

USER appuser

# No EXPOSE or HEALTHCHECK: worker is background job processor
CMD ["python", "-m", "worker.backend_worker"]

# ============================================================
# STAGE 5: MCP Server
# ============================================================
FROM base as mcp_server

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY mcp_server/ ./mcp_server/
COPY mcp_tools/ ./mcp_tools/
COPY shared/ ./shared/
COPY pyproject.toml ./
COPY VERSION.json ./
COPY LICENSES/ ./LICENSES/
COPY DEPENDENCIES.md ./DEPENDENCIES.md

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 7000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7000/healthz || exit 1

CMD ["uvicorn", "mcp_server.app:app", "--host", "0.0.0.0", "--port", "7000"]

# ============================================================
# STAGE 6: Default target (control_plane)
# ============================================================
FROM control_plane as latest