# Multi-stage build for worker service
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir requests PyJWT cryptography psycopg[binary] redis typer PyYAML

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY control_plane/ ./control_plane/
COPY worker/ ./worker/
COPY shared/ ./shared/
COPY pyproject.toml ./

RUN adduser --uid 5678 --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

USER appuser

# No EXPOSE as this is a background worker, no HEALTHCHECK needed as it's job-based

CMD ["python", "-m", "worker.backend_worker"]
