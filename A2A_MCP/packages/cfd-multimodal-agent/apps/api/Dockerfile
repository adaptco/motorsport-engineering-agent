FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "cfd_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
