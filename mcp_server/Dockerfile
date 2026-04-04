FROM python:3.11-slim
WORKDIR /app
COPY mcp_server/ ./mcp_server/
COPY mcp_tools/ ./mcp_tools/
COPY shared/ ./shared/
COPY pyproject.toml ./
COPY VERSION.json ./
RUN pip install --no-cache-dir fastapi uvicorn pydantic
ENV PYTHONPATH=/app
CMD ["uvicorn", "mcp_server.app:app", "--host", "0.0.0.0", "--port", "7000"]
