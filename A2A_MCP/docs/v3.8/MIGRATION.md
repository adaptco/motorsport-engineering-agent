# V3.8 Migration

## Additions

- new package: `packages/cfd-multimodal-agent`
- new package: `packages/cfd-contracts`
- new compose file: `docker-compose.v3_8.yml`
- new env example: `infra/env/cfd-multimodal-agent.env.example`
- new top-level make targets for local workflow

## No breaking changes

V3.8 does not modify:
- existing MCP runtime contracts
- current agent orchestration paths
- registry ownership
- state machine semantics

## Apply order

1. create directory structure
2. add contracts package
3. add API package
4. add web package
5. add compose + env + docs
6. run API tests
7. run web build
