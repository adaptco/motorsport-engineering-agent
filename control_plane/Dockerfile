FROM python:3.11-slim
WORKDIR /app
COPY control_plane/ ./control_plane/
COPY shared/ ./shared/
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn pydantic requests PyJWT cryptography psycopg[binary] redis typer PyYAML
ENV PYTHONPATH=/app
CMD ["uvicorn", "control_plane.app:app", "--host", "0.0.0.0", "--port", "8000"]
