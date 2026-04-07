# AXP Protocol Next Artifacts

This bundle fills the missing production-layer artifacts after the Day 0 foundation bundle:

- `anp-route-decision.schema.json`
- `acp-handoff-envelope.schema.json`
- `acp-execution-receipt.schema.json`
- `acp-commit-receipt.schema.json`
- `workflow-cursor.schema.json`
- `stage-a-lexer-spec.md`
- `protocol-compatibility-policy.md`

Design decisions:

- separate execution and commit receipts
- explicit authority binding on protocol-bearing fields
- resumable cursor as source of truth
- Stage A lexer spec before prose tokenization
- conservative compatibility policy with hash stability rules
