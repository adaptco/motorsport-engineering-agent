# Protocol Compatibility Policy

Version: 1.0.0

## Scope

This policy governs compatibility for:

- `ANP.RouteDecision`
- `ACP.HandoffEnvelope`
- `ACP.ExecutionReceipt`
- `ACP.CommitReceipt`
- `ACP.WorkflowCursor`
- Stage A lexer output

## Stability rule

Major version `1.x` is a closed wire family.
No field may become optional, change meaning, or change token mapping within `1.x`.

## Compatibility matrix

### Patch release

Allowed:

- typo fixes in descriptions
- tighter examples
- additional documentation
- stricter validators that do not reject previously valid objects

Not allowed:

- new required fields
- changed enum meanings
- changed token spellings

### Minor release

Allowed only when backward-compatible:

- new optional fields
- new enum members if old parsers can safely reject or ignore them by policy
- new reason codes
- new documentation sections

Required:

- `min_supported` must remain within same major version
- Stage A mappings for existing objects must remain identical

### Major release

Required for:

- field removal
- field rename
- semantic reinterpretation
- enum repurposing
- token family changes
- canonical field order changes
- receipt hash computation changes

## Reader/writer policy

- Readers must reject objects with a higher **major** version.
- Readers may accept higher **minor** versions only if all unknown fields are optional and policy marks them ignorable.
- Writers must emit the lowest version that fully represents the object.
- Mixed-version workflows are allowed only when `compatibility.min_supported <= peer.current <= compatibility.max_emittable`.

## Hash stability

The following are hash-stable across all `1.x` versions:

- receipt hash field names
- cursor hash field names
- canonical field order for Stage A
- token spellings for all reserved atoms

Any change to these requires a major version bump.

## Tool registry conflict rules

When multiple tools advertise overlapping capability tags:

1. exact `tool_id` uniqueness is mandatory
2. exact `display_name` duplication is forbidden within one registry scope
3. precedence order is:
   - session-specific tool pool
   - agent-local registry
   - inherited parent registry
   - global registry
4. `enabled_by_default=false` tools may never shadow enabled tools without explicit policy
5. destructive tools may not be selected purely by capability overlap; explicit `tool_id` selection is required

## Receipt compatibility

`ACP.ExecutionReceipt` and `ACP.CommitReceipt` are distinct wire contracts.
Execution success does not imply commit success.
Cursor advancement is valid only from a compatible `ACP.CommitReceipt`.

## Failure-path planning

On version mismatch:

- emit structured reason code
- do not attempt prose fallback
- do not infer missing fields
- preserve existing cursor
- record the incompatibility in structured logs

## Non-negotiable invariant

No protocol action may be derived from transcript commentary when a typed compatible object exists.
