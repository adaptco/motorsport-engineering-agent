# MCP / LLM Provider Scaffold

The A2A MCP scaffold exposes provider metadata but does not proxy real model calls until valid API keys are present.

## Supported scaffolded providers

- `openai` → `OPENAI_API_KEY`
- `anthropic` → `ANTHROPIC_API_KEY`
- `google` → `GOOGLE_API_KEY`
- `openrouter` → `OPENROUTER_API_KEY`

## Shared gateway token

Requests to the MCP server may optionally include:

- `Authorization: Bearer ${MCP_SHARED_BEARER_TOKEN}`

## Endpoints

- `GET /providers`
- `POST /a2a/invoke`
- `POST /tools/call`
