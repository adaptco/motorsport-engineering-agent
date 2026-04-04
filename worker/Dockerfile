FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY control_plane/ ./control_plane/
COPY worker/ ./worker/
COPY shared/ ./shared/
COPY pyproject.toml ./
COPY VERSION.json ./
RUN pip install --no-cache-dir requests PyJWT cryptography psycopg[binary] redis typer PyYAML
ENV PYTHONPATH=/app
CMD ["python", "-m", "worker.backend_worker"]
