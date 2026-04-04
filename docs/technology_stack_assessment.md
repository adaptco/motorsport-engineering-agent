# Technology Stack and Dependencies Assessment

## Python Version
- Required: >= 3.11
- Current: 3.13.7 (verified compatible)

## Key Libraries
From pyproject.toml:
- fastapi>=0.115.0 (Web framework)
- uvicorn[standard]>=0.30.0 (ASGI server)
- pydantic>=2.8.0 (Data validation)
- psycopg[binary]>=3.2.0 (PostgreSQL driver)
- redis>=5.0.0 (Redis client)
- httpx>=0.27,<1 (HTTP client)
- PyJWT>=2.9.0 (JWT handling)
- cryptography>=43.0.0 (Cryptographic functions)
- typer>=0.12.0 (CLI framework)
- PyYAML>=6.0.0 (YAML parsing)

Development dependencies:
- pytest>=8.3.0 (Testing framework)
- pytest-cov>=5.0.0 (Coverage reporting)

## Infrastructure Dependencies
From docker-compose.yml:
- PostgreSQL 16 (Database)
- Redis 7 (Caching/Message queue)
- Docker containers for control plane, worker, and MCP server

## External API Integrations
- GitHub API (via github_app_client.py for repository management, webhooks, PR handling)
- LLM Providers (OpenAI, Anthropic, Google, OpenRouter via MCP server)
- iRacing telemetry streams (data ingestion)

## Development Tools and Frameworks
- Docker & Docker Compose (Containerization)
- Makefile (Build automation)
- pytest (Unit testing)
- FastAPI (REST API framework)
- Pydantic (Data models)
- Uvicorn (Server)
- Typer (CLI tools)

## Verification
- Python version check: PASSED
- Core dependencies import: PASSED
- All infrastructure services defined in compose files
- External integrations identified in codebase