# Repo patch manifest for MEA V3.8

## Add
- contracts/runtime/agent_runtime_contract_bundle.schema.json
- contracts/runtime/README.md
- deploy/containers/mea-v3.8/Dockerfile
- deploy/compose/docker-compose.v3.8.yml
- docs/REPO_SNAPSHOT_2026-04-07.md
- tests/test_runtime_contract_bundle.py
- tests/test_runtime_event_order.py

## Modify
- PRD.md
- VERSION.json
- pyproject.toml
- control_plane/app.py
- control_plane/queue.py
- control_plane/services/mcp_client.py
- worker/backend_worker.py
- shared/db.py
- docker-compose.yml
- control_plane/Dockerfile
- worker/Dockerfile
- mcp_server/Dockerfile

## Delete or deprecate
- Dockerfile
