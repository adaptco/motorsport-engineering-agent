#!/usr/bin/env python3
"""Reject stale MEA V3.x release references and unpinned MEA image tags.

This checker is invoked by pre-commit and CI. It deliberately excludes generated
lockfiles and binary content, while scanning every other tracked text file passed
by pre-commit. The policy protects MEA product/runtime references only; external
tool versions such as GitHub Actions are outside its scope.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

LEGACY_VERSION_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_])v3\.[0-7](?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])0\.3\.[0-7](?![A-Za-z0-9_])"),
)
UNPINNED_IMAGE_PATTERNS = (
    re.compile(r"\bmea-[a-z0-9-]+:latest\b", re.IGNORECASE),
    re.compile(r"\$\{VERSION:-latest\}"),
    re.compile(r"\bmotor(?:sport)?engineeringagent:latest\b", re.IGNORECASE),
    re.compile(r"\b(?:your-registry/)?(?:control-plane|worker|mcp-server):latest\b"),
)
EXCLUDED_FILENAMES = {"package-lock.json", "uv.lock"}
THIRD_PARTY_ACTION_PATTERN = re.compile(
    r"^\s*uses:\s*[^\s]+@v3\.[0-7](?:\.\d+)?\s*$", re.IGNORECASE
)
BINARY_BYTES = b"\x00"


def _iter_violations(path: Path) -> Iterable[str]:
    """Yield one descriptive violation per matching line in a text file."""
    if path.name in EXCLUDED_FILENAMES or not path.is_file():
        return

    content = path.read_bytes()
    if BINARY_BYTES in content:
        return

    text = content.decode("utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if THIRD_PARTY_ACTION_PATTERN.match(line):
            continue
        for pattern in (*LEGACY_VERSION_PATTERNS, *UNPINNED_IMAGE_PATTERNS):
            if pattern.search(line):
                yield f"{path}:{line_number}: stale V3.x or unpinned latest MEA reference: {line.strip()}"
                break


def main(paths: list[str]) -> int:
    """Report policy violations for paths supplied by pre-commit."""
    violations = [violation for raw_path in paths for violation in _iter_violations(Path(raw_path))]
    if not violations:
        return 0

    print("MEA V3.8 runtime-reference policy failed:", file=sys.stderr)
    print(*violations, sep="\n", file=sys.stderr)
    print(
        "Pin MEA runtime references to V3.8 (kernel 3.8/package 0.3.8) and use explicit image tags.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
