# Stage A Lexer Spec

Version: 1.0.0

## Purpose

Stage A converts **authoritative typed protocol objects** into a closed token stream before any prose tokenization occurs.
It is the authority-preserving layer for ANP, ACP, A2A, and MCP state.

## Control law

- No protocol action may be derived from prose when a typed object exists.
- Stage A tokens are authoritative only when `authority_binding.authority == authoritative`.
- Stage B prose tokens are never sufficient for route, commit, receipt verification, or cursor advancement.

## Input classes

Accepted object kinds:

- `ANP.RouteDecision`
- `ACP.HandoffEnvelope`
- `ACP.ExecutionReceipt`
- `ACP.CommitReceipt`
- `ACP.WorkflowCursor`

Objects outside this set are rejected.

## Output model

The lexer emits an ordered stream of canonical atoms:

- `@NS:<family>`
- `@TYPE:<object_type>`
- `@VERB:<verb>`
- `@KEY:<field_name>`
- `@VAL:<typed_atom>`
- `@SIG:<sha256>`

## Atom families

- `NS`
- `TYPE`
- `VERB`
- `KEY`
- `ENUM`
- `REF`
- `HASH`
- `NUM`
- `TIME`
- `BOOL`
- `NULL`
- `ERR`
- `INVARIANT`

## Normalization rules

### 1. Namespace

Map `kind` to namespace:

- `ANP.* -> @NS:ANP`
- `ACP.* -> @NS:ACP`
- `A2A.* -> @NS:A2A`
- `MCP.* -> @NS:MCP`

### 2. Type

Emit exact upper snake tokens:

- `ANP.RouteDecision -> @TYPE:ANP.ROUTE_DECISION`
- `ACP.HandoffEnvelope -> @TYPE:ACP.HANDOFF_ENVELOPE`
- `ACP.ExecutionReceipt -> @TYPE:ACP.EXECUTION_RECEIPT`
- `ACP.CommitReceipt -> @TYPE:ACP.COMMIT_RECEIPT`
- `ACP.WorkflowCursor -> @TYPE:ACP.WORKFLOW_CURSOR`

### 3. Verb

Verb is derived from object kind and status:

- `ANP.RouteDecision -> @VERB:RESOLVE`
- `ACP.HandoffEnvelope(intent=task.submit) -> @VERB:SUBMIT`
- `ACP.HandoffEnvelope(intent=task.resume) -> @VERB:RESUME`
- `ACP.ExecutionReceipt -> @VERB:EMIT_EXECUTION_RECEIPT`
- `ACP.CommitReceipt(status=committed) -> @VERB:COMMIT`
- `ACP.CommitReceipt(status=rejected) -> @VERB:REJECT`
- `ACP.WorkflowCursor -> @VERB:CHECKPOINT`

### 4. Field order

Fields must be emitted in canonical order:

1. identity fields
2. routing/session fields
3. authority fields
4. budget fields
5. receipt/hash fields
6. decision/status fields
7. signature/hash footer

If an input object is unordered, the lexer reorders it.

### 5. Scalar mapping

- identifiers -> `@REF:<value>`
- sha256 -> `@HASH:<value>`
- timestamps -> `@TIME:<iso8601>`
- integers/decimals -> `@NUM:<normalized>`
- booleans -> `@BOOL:true|false`
- null -> `@NULL`
- enums -> `@ENUM:<namespace.value>`

### 6. Arrays

Arrays are emitted as repeated `@KEY/@VAL` pairs in sorted order when order is not semantically significant.
For semantically ordered arrays, preserve input order.

### 7. Authority bit

Every emitted field must carry an internal authority label:

- `authoritative`
- `derived`
- `commentary`

Only `authoritative` fields may drive:

- route resolution
- handoff admission
- receipt verification
- cursor advancement
- budget admission

## Rejection conditions

Reject input when any of the following are true:

- missing required field
- undeclared field present
- enum value outside registry
- identifier violates pattern
- authoritative field sourced from commentary
- required receipt hash missing
- cursor advancement attempted without commit receipt

## Example

Input:

```json
{
  "kind": "ACP.HandoffEnvelope",
  "workflow_id": "wf_demo",
  "task_id": "T005",
  "intent": "task.submit"
}
```

Output atom prefix:

```text
@NS:ACP
@TYPE:ACP.HANDOFF_ENVELOPE
@VERB:SUBMIT
@KEY:workflow_id @VAL:@REF:wf_demo
@KEY:task_id @VAL:@REF:T005
@KEY:intent @VAL:@ENUM:INTENT.TASK_SUBMIT
```

## Commit boundary

Stage A output is the canonical protocol-bearing stream.
Stage B prose tokenization must run **after** Stage A and cannot overwrite Stage A atoms.
