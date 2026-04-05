# Environment Reference

## Core Service Configuration

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `CONTROL_PLANE_PORT` | No | `8000` | Control plane listen port |
| `MCP_PORT` | No | `7000` | MCP server listen port |
| `DATABASE_URL` | Yes | `postgresql://mea:mea@postgres:5432/mea` | Postgres connection string |
| `REDIS_URL` | Yes | `redis://redis:6379/0` | Redis connection string |
| `SESSION_LEDGER_DB_PATH` | Yes | workspace `.mea_tmp/workflow_state/session-ledger.db` | Durable forensic session-ledger SQLite path |

## DB Connectivity and Pooling

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DB_CONNECT_TIMEOUT_SECONDS` | No | `10` | Connect timeout for direct DB connections |
| `DB_POOL_ENABLED` | No | `true` | Enable psycopg pool path |
| `DB_POOL_MIN_SIZE` | No | `1` | Minimum pool size |
| `DB_POOL_MAX_SIZE` | No | `10` | Maximum pool size |
| `DB_POOL_TIMEOUT_SECONDS` | No | `30` | Pool checkout timeout |
| `DB_POOL_MAX_WAITING` | No | `20` | Max waiting clients for pool |

## Queue and Redis Behavior

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `QUEUE_ALLOW_IN_MEMORY_FALLBACK` | No | `true` | Allow in-memory queue fallback when Redis is unavailable |
| `REDIS_CB_FAILURE_THRESHOLD` | No | `3` | Circuit-breaker consecutive failure threshold |
| `REDIS_CB_RECOVERY_TIMEOUT_SECONDS` | No | `30` | Circuit-breaker open timeout before retry |

## GitHub App

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GITHUB_APP_ID` | Yes | none | GitHub App ID |
| `GITHUB_APP_INSTALLATION_ID` | Yes | none | GitHub App installation ID |
| `GITHUB_APP_PRIVATE_KEY` | Yes | none | PEM private key for JWT signing |
| `GITHUB_WEBHOOK_SECRET` | Yes | none | GitHub webhook signature secret |
| `GITHUB_ALLOWED_REPOS` | Yes | none | Allowlist of repos for CI worker actions |
| `GITHUB_API_MAX_RETRIES` | No | `2` | Bounded retries for token issuance |
| `GITHUB_API_CB_FAILURE_THRESHOLD` | No | `3` | Circuit-breaker consecutive failure threshold |
| `GITHUB_API_CB_RECOVERY_TIMEOUT_SECONDS` | No | `30` | Circuit-breaker open timeout before retry |

## MCP and LLM Bridge

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MCP_SHARED_BEARER_TOKEN` | No | empty | Shared bearer token for MCP server protection |
| `MCP_SERVER_BASE_URL` | No | `http://localhost:7000` | MCP call target base URL |
| `MCP_API_MAX_RETRIES` | No | `2` | Bounded retries for MCP calls |
| `MCP_API_CB_FAILURE_THRESHOLD` | No | `3` | Circuit-breaker consecutive failure threshold |
| `MCP_API_CB_RECOVERY_TIMEOUT_SECONDS` | No | `30` | Circuit-breaker open timeout before retry |
| `OPENAI_API_KEY` | No | empty | OpenAI provider key |
| `ANTHROPIC_API_KEY` | No | empty | Anthropic provider key |
| `GOOGLE_API_KEY` | No | empty | Google provider key |
| `OPENROUTER_API_KEY` | No | empty | OpenRouter provider key |

## Worker Limits

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MAX_PATCH_LINES` | No | `1000` | Maximum accepted patch size |
| `ALLOW_WORKFLOW_CHANGES` | No | `false` | Allow CI worker edits under `.github/workflows` |

## A2A State Persistence

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `A2A_WORKFLOW_STATE_DIR` | No | `.mea_tmp/workflow_state` | Persisted workflow-state directory |
| `A2A_WORKFLOW_STATE_SCHEMA` | No | `contracts/a2a/workflow_state.schema.json` | Workflow-state contract schema path |
| `A2A_WORKFLOW_STATE_MAX_HISTORY` | No | `50` | History retention for workflow state snapshots |
