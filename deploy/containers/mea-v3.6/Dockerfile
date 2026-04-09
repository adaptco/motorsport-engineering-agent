FROM python:3.11-slim

# MEA V3.6 container cut
# This Dockerfile builds the runtime contract harness as a minimal image. It expects
# the runtime package and contracts to be copied in at build time.

# Copy source and contracts
COPY contracts/runtime/agent_runtime_contract_bundle.schema.json /app/contracts/runtime/agent_runtime_contract_bundle.schema.json

# Install dependencies required for runtime contract validation and core services.
RUN pip install --no-cache-dir fastapi pydantic uvicorn==0.23.*

# Set the working directory and expose default port.
WORKDIR /app
EXPOSE 8080

# Default command starts the HTTP server. The underlying application should provide
# endpoints for validating and serving contract events.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]