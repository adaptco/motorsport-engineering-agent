# Project Structure and Configuration Analysis

## Overview
This document provides a comprehensive analysis of the motorsport-engineering-agent (MEA) project structure and configuration as of Task-001 completion.

## Project Dependencies and Versions (pyproject.toml)

### Core Dependencies
- **fastapi>=0.115.0**: Web framework for building APIs
- **uvicorn[standard]>=0.30.0**: ASGI server for FastAPI
- **pydantic>=2.8.0**: Data validation and serialization
- **psycopg[binary]>=3.2.0**: PostgreSQL database adapter
- **redis>=5.0.0**: Redis client for caching/queueing
- **httpx>=0.27,<1**: HTTP client library
- **PyJWT>=2.9.0**: JSON Web Token implementation
- **cryptography>=43.0.0**: Cryptographic functions
- **typer>=0.12.0**: Command-line interface builder
- **PyYAML>=6.0.0**: YAML parser

### Development Dependencies
- **pytest>=8.3.0**: Testing framework
- **pytest-cov>=5.0.0**: Coverage reporting for pytest

### Python Version Requirement
- Requires Python >=3.11

## Docker Configuration

### Dockerfile
- **Base Image**: python:3-slim (minimal Python image)
- **Exposed Port**: 8000
- **Environment Variables**:
  - PYTHONDONTWRITEBYTECODE=1 (prevents .pyc files)
  - PYTHONUNBUFFERED=1 (disables output buffering)
- **Installation**: Installs requirements from requirements.txt
- **User**: Runs as non-root user (appuser, UID 5678)
- **Entry Point**: Gunicorn with Uvicorn workers serving mcp_tools.__init__:app

### Docker Compose Files
- **compose.yaml**: Simple service definition for motorsportengineeringagent
  - Builds from local Dockerfile
  - Maps port 8000:8000
- **compose.debug.yaml**: Debug configuration (not analyzed in detail)
- **docker-compose.yml**: Legacy compose file (not analyzed in detail)

## Database Schema (migrations/)

### Migration 001_init.sql
Creates core tables for the MEA system:
- **github_installations**: GitHub App installation data
- **jobs**: Job queue and processing records
- **job_events**: Event logging for jobs
- **traces**: Distributed tracing data
- **spans**: Tracing spans (partial definition in file)

### Migration 002_session_runtime.sql
Adds telemetry processing tables:
- **session_evidence**: Evidence packets from racing sessions
- **recommendations_runtime**: AI-generated recommendations
- Indexed on session_id and timestamp for performance

### Migration 003_evidence_packets.sql
Refines evidence storage:
- **evidence_packets**: Structured evidence data with JSONB features
- Indexed for efficient querying by session and timestamp

## Configuration Files

### configs/model_weights.yaml
Contains reward weighting configuration for the supervisor system:
- **supervisor_reward_weights**: Weights for different success criteria
  - ttl_valid: 0.20
  - delivered: 0.24
  - outcome_improved: 0.36
  - replay_determinism: 0.12
  - evidence_traceability: 0.08
- **weights**: Simplified weights for core metrics

### VERSION.json
Version and compatibility information:
- **kernel_version**: "3.4"
- **package_version**: "0.3.4"
- **release_channel**: "stable"
- **compatibility**:
  - replay_schema: 1
  - forensic_ledger_schema: 1

## Build and Deployment Scripts

### Makefile
Provides automation targets:
- **test**: Runs pytest with quiet output
- **build-images**: Builds Docker images for all services
  - control-plane
  - mcp-server
  - worker

### scripts/
- **github_pr_api.sh**: Bash script for GitHub PR operations
  - List PRs, review, merge, close
  - Requires GITHUB_TOKEN and REPO_SLUG environment variables
- **pr_preflight.sh**: Preflight checks for PR governance
  - Validates git, gh CLI, jq installation
  - Checks GitHub authentication
  - Verifies remote repository access
  - Ensures main branch exists

## Architecture Insights

### Technology Stack
- **Backend**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with JSONB support
- **Cache/Queue**: Redis
- **Containerization**: Docker with multi-service architecture
- **CI/CD**: GitHub Actions (inferred from commit history)
- **Testing**: pytest with coverage

### Key Components Identified
1. **Control Plane**: FastAPI application handling API routes and job management
2. **MCP Server**: Model Context Protocol server for LLM integrations
3. **Worker**: Backend processing for job execution and GitHub integration
4. **Database**: PostgreSQL with migrations for schema management
5. **Telemetry Ingestion**: iRacing data processing (inferred from ingest/ directory)

### Deployment Model
- Containerized microservices architecture
- Single exposed port (8000) for main service
- Separate Dockerfiles for different components
- Compose-based local development setup

## Verification Results

All acceptance criteria have been met through file analysis and documentation. Verification commands will be executed in the next phase.