"""ingest/logs/adapters/pi_mat module."""

from __future__ import annotations

from pathlib import Path

from scipy.io import loadmat  # type: ignore[import]

from ingest.logs.types import ParsedLog
from ingest.logs.util import flatten_mat_dict


def parse_pi_mat(path: Path) -> ParsedLog:
    if path.suffix.lower() == ".pds":
        raise RuntimeError(
            "Native Pi .pds decoding is not included in V3.8. Use Pi Toolbox Pro MAT export for initial testing."
        )
    raw = loadmat(path)
    frame = flatten_mat_dict(raw)
    return ParsedLog(
        vendor="pi",
        source_path=path,
        frame=frame,
        metadata={"parser": "scipy.io.loadmat"},
        notes=[
            "Pi MAT export adapter; preferred public path for Pi/Cosworth sessions when not using a native .pds decoder."
        ],
    )
