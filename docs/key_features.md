# Key Features and Capabilities

## Overview

The Motorsport Engineering Agent (MEA) is a comprehensive system that integrates AI-driven decision-making with motorsport telemetry data processing, particularly from the iRacing simulator. It provides automated CI fixing, replay analysis, session management, and GitHub integration for motorsport engineering workflows.

## Core Features

### CI Fixing
- Automated patch validation and application to fix CI failures
- Security checks to prevent injection of sensitive data (tokens, keys)
- Workflow file modification controls for safety
- GitHub PR integration for seamless code fixes
- Command execution in isolated environments

### Replay Analysis
- JSONL telemetry frame validation and processing
- Replay metrics calculation (frame counts, timing analysis, channel validation)
- Compressed timeline reconstruction for performance analysis
- Deterministic replay verification ensuring consistent outputs
- Support for iRacing telemetry streams with configurable sampling rates

### Session Management
- Evidence batch ingestion and storage
- Session ledger replay functionality
- Forensic audit trails with receipt logging
- Session runtime tracking and evidence packets
- Multi-session coordination for complex analysis workflows

## AI Decision-Making Capabilities

### Agent Decision API
- Supervisor service for queuing and processing AI decisions
- Support for multiple LLM providers (OpenAI, Anthropic, Google, OpenRouter)
- Policy engine for decision authorization and validation
- Forensic ledger integration for decision traceability
- Time domain reasoning for temporal analysis

### MCP Server Integration
- Model Context Protocol (MCP) server for AI tool orchestration
- CI guardrail tools for automated code quality enforcement
- A2A (Agent-to-Agent) invoke functionality for distributed processing
- Authentication and authorization mechanisms

## Telemetry Processing Features

### iRacing Stream Ingestion
- Real-time telemetry frame streaming from iRacing simulator
- Channel mapping and data normalization
- Quality flag tracking for data integrity
- Configurable sampling rates (default 60Hz)
- Error handling for simulator unavailability

### Data Validation
- JSONL schema validation for telemetry artifacts
- Frame-by-frame validation with error counting
- Required channel verification (Throttle, Brake, Speed)
- Timestamp and tick sequence validation

## GitHub Integration Features

### GitHub App Integration
- JWT-based authentication for GitHub App operations
- Installation token generation for repository access
- Webhook processing for PR events and CI status updates
- Repository management with allowed repo restrictions
- PR creation and management through GitHub API

### Webhook Handling
- Event-driven processing for GitHub webhooks
- Queue-based job processing for scalability
- Error handling and retry mechanisms
- Audit logging for all webhook interactions

## Performance Metrics and Monitoring

### Performance Tasks
- **Replay Determinism**: Ensures identical outputs across replay runs (threshold: 100%)
- **Policy Latency**: Decision processing time under 5ms threshold
- **JSONL Schema Validation**: Zero invalid lines allowed
- **Supervisor Loop Acceptance**: Minimum 2 paired receipts for audit completeness

### Release Validation
- Automated pytest execution (17 passed, 1 warning in 5.94s)
- Git commit and tag tracking for version control
- Source lineage documentation for traceability
- Bundle validation for deployment integrity

### Monitoring Capabilities
- Health check endpoints for all services
- Component import verification
- Docker container health monitoring
- Database connection and migration validation

## Technology Stack Integration

- **Backend**: FastAPI for REST APIs, Uvicorn for ASGI server
- **Database**: PostgreSQL with custom migrations, Redis for queuing
- **AI/ML**: Multiple LLM provider support via MCP
- **Infrastructure**: Docker containers, docker-compose orchestration
- **Versioning**: Semantic versioning with release manifests
- **Testing**: Pytest with comprehensive unit and integration tests