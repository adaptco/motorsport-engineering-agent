# ANP / AXP Protocol Assets

This folder contains imported protocol artifacts for the Agent Network Protocol (ANP) and Agent Communication Protocol (ACP), plus AXP foundational assets.

## Sources

- `axp-protocol-next.zip`
- `axp-harness-bundle.zip`

## Layout

- `contracts/anp/schemas/`: ANP/ACP wire schemas and shared AXP defs.
- `contracts/anp/examples/`: Example payloads for route decisions, handoffs, cursor, and receipts.
- `contracts/axp/schemas/`: AXP foundational bundle schema.
- `contracts/axp/dictionaries/`: Canonical token dictionary.

## Validation

Run:

```bash
pytest -q tests/test_anp_contract_bundle.py
```

This verifies:

- all imported files exist
- ANP/ACP examples validate against their schemas
- AXP foundational schema and token dictionary are structurally present
