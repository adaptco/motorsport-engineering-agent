# V3.1 Codebase Review

## Finding

The two `0.3.1` artifacts are **not merge-clean under the same version number**.

## Divergence summary

### `Root-Kernel-V3.1.zip`
- includes `shared/forensic_ledger.py`
- includes `control_plane/routes/verifier.py`
- includes `control_plane/services/job_runner.py`
- includes tests for verifier + forensic ledger
- does **not** include `db/migrations/003_session_receipts.sql`

### `Root-Kernel-V3.1-source.zip` and patch
- includes `control_plane/services/session_receipts.py`
- includes `db/migrations/003_session_receipts.sql`
- includes `GET /session/{session_id}/replay-ledger`
- includes Antigravity worktree bootstrap docs
- does **not** include verifier route or job runner

## Conclusion

The V3.1 artifacts were divergent and should not have shared the same version label.

## Resolution

- canonicalize on a new merged release: **V3.2 / 0.3.2**
- preserve additive APIs from both lines
- keep deterministic replay as the release gate
