FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    MEA_KERNEL_VERSION=3.6 \
    MEA_PACKAGE_VERSION=0.3.6

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml VERSION.json ./
COPY control_plane/ ./control_plane/
COPY worker/ ./worker/
COPY mcp_server/ ./mcp_server/
COPY mcp_tools/ ./mcp_tools/
COPY shared/ ./shared/
COPY ingest/ ./ingest/
COPY contracts/ ./contracts/
COPY frontend/ ./frontend/

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir \
       fastapi \
       "uvicorn[standard]" \
       pydantic \
       jsonschema \
       referencing \
       "psycopg[binary]" \
       redis \
       requests \
       PyJWT \
       cryptography \
       typer \
       PyYAML \
       pandas \
       scipy \
       gunicorn

RUN useradd --system --create-home --uid 10001 mea \
    && chown -R mea:mea /app

USER mea

EXPOSE 8000 7000

CMD ["uvicorn", "control_plane.app:app", "--host", "0.0.0.0", "--port", "8000"]
