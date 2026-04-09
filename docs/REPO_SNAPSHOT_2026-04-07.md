# Repository Snapshot as of 2026‑04‑07

This snapshot captures the state of the `adaptco/motorsport‑engineering‑agent` repository before applying
version 3.6 changes. The default branch at the time of snapshot was `main` at commit
`d010752cbf859221e55a905b715ef4983b301f08`.

## Notable Files

- **VERSION.json** – lists the kernel and package versions (`3.5.2` / `0.3.5.2`).
- **pyproject.toml** – defines the package version (`0.3.5.2`).
- **control_plane/app.py**, **control_plane/queue.py** – existing control‑plane entrypoints without the new runtime harness integration.
- **PRD.md** – design document describing the v3.6 contract harness and container cut.

## Purpose

This snapshot document ensures there is a persistent record of the baseline repository state prior
to introducing MEA v3.6. It allows reviewers to verify that the patch applies cleanly and avoids
merge conflicts or destructive actions.