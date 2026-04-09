"""ingest/logs/adapters/vbox_vbo module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingest.logs.types import ParsedLog
from ingest.logs.util import coerce_numeric_columns


VBOX_HEADER_MARKER = "[column names]"


def parse_vbox_vbo(path: Path) -> ParsedLog:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if line.strip().lower().startswith(VBOX_HEADER_MARKER):
            header_index = index
            break
    if header_index is None:
        raise ValueError("VBOX .vbo file missing [column names] header marker")
    columns = lines[header_index + 1].strip().split()
    data_lines = [line for line in lines[header_index + 2 :] if line.strip()]
    rows = [row.split() for row in data_lines]
    frame = pd.DataFrame(rows, columns=columns)
    frame = coerce_numeric_columns(frame)
    return ParsedLog(
        vendor="vbox",
        source_path=path,
        frame=frame,
        metadata={"parser": "vbox_text"},
        notes=["Parsed from VBOX standard space-delimited text log."],
    )
