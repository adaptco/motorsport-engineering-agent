repo/
├── apps/
│   ├── control-plane/
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── sessions.py
│   │   │   │   ├── runs.py
│   │   │   │   ├── telemetry.py
│   │   │   │   ├── evals.py
│   │   │   │   └── health.py
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── mcp-gateway/
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── tools.py
│   │   │   │   ├── providers.py
│   │   │   │   └── a2a.py
│   │   │   └── app.py
│   │   └── Dockerfile
│   └── hitl-console/
│       ├── src/
│       ├── public/
│       └── Dockerfile
├── services/
│   ├── orchestrator/
│   │   ├── src/
│   │   │   ├── loop/
│   │   │   ├── handoff/
│   │   │   ├── planning/
│   │   │   ├── receipts/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── telemetry-ingest/
│   │   ├── src/
│   │   │   ├── adapters/
│   │   │   ├── normalize/
│   │   │   ├── sampling/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── memory/
│   │   ├── src/
│   │   │   ├── state_store/
│   │   │   ├── vector_store/
│   │   │   ├── retrieval/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── eval-engine/
│   │   ├── src/
│   │   │   ├── rubrics/
│   │   │   ├── scoring/
│   │   │   ├── hitl/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── ledger/
│   │   ├── src/
│   │   │   ├── canonicalize/
│   │   │   ├── append_only/
│   │   │   ├── replay/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── agent-supervisor/
│   │   ├── src/
│   │   │   ├── prompts/
│   │   │   ├── policies/
│   │   │   └── app.py
│   │   └── Dockerfile
│   ├── agent-telemetry-analyst/
│   │   ├── src/
│   │   │   ├── prompts/
│   │   │   ├── heuristics/
│   │   │   └── app.py
│   │   └── Dockerfile
│   └── agent-replay-analyst/
│       ├── src/
│       │   ├── prompts/
│       │   ├── evaluators/
│       │   └── app.py
│       └── Dockerfile
├── contracts/
│   ├── orchestration/
│   ├── a2a/
│   ├── telemetry/
│   ├── evals/
│   ├── receipts/
│   └── policy/
├── packages/
│   ├── sdk-models/
│   ├── sdk-client/
│   └── ui-components/
├── deploy/
│   ├── compose/
│   ├── k8s/
│   └── helm/
├── config/
│   ├── agents/
│   ├── models/
│   ├── tools/
│   └── policy/
├── tests/
│   ├── contracts/
│   ├── integration/
│   ├── replay/
│   ├── evals/
│   └── smoke/
└── docs/
    ├── architecture/
    ├── runbooks/
    └── adr/
