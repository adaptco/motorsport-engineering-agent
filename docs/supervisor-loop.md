# Supervisor Loop

The supervisor loop is the core decision-making mechanism of the Motorsport Engineering Agent (MEA). It processes AI agent decision requests, integrates reasoning components, and ensures forensic accountability through the ledger system.

## API Endpoint

`POST /agent/decision` accepts an evidence-bound decision request and records paired forensic receipts before and after queueing the supervisor job.

### Process Flow

1. **Intent Logging**: Before processing, the request is logged to the forensic ledger with `receipt_type='agent_decision_intent'` and status 'ACCEPTED'.
2. **Job Queuing**: The decision request is queued via `queue_agent_decision(req)` from the supervisor service.
3. **Result Logging**: After processing, the result is logged to the ledger with `receipt_type='agent_decision_result'`.

## Reasoning Components

### Policy Engine

The `PolicyEngine` class manages recommendations with the following features:

- **Priority Queue**: Recommendations are prioritized from CRITICAL (0) to NONE (4), processed oldest-first within priority levels.
- **TTL (Time To Live)**: Recommendations expire after 2 seconds by default.
- **Cooldown**: Prevents delivery of non-critical recommendations within 3 seconds of the last delivery.
- **Thread-Safe**: Uses RLock for concurrent access.

### Time Domains

The system distinguishes between two time domains:

- **DATA**: Simulator/logical time (monotonic, dense, near the run's timeline).
- **WALL**: Wall-clock/Unix time (timestamps > 1e18 nanoseconds).

Time domain inference is based on timestamp magnitude and logical clock context.

## Required Provider Keys

- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY
- OPENROUTER_API_KEY

## Integration

The supervisor loop integrates with:
- Control plane routes (agent.py)
- Supervisor service (queue_agent_decision)
- Forensic ledger (append_receipt)
- Worker backend for job processing
