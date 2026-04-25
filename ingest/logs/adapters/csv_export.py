"""ingest/logs/adapters/csv_export module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingest.logs.types import ParsedLog
from ingest.logs.util import coerce_numeric_columns, infer_delimiter


def parse_csv_export(path: Path, vendor: str = "csv_export") -> ParsedLog:
    delimiter = infer_delimiter(path)
    frame = pd.read_csv(path, sep=delimiter, engine="python")
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = coerce_numeric_columns(frame)
    return ParsedLog(
        vendor=vendor,
        source_path=path,
        frame=frame,
        metadata={"parser": "pandas.read_csv", "delimiter": delimiter or "auto"},
        notes=[
            "CSV/TXT export adapter; use for Haltech/AEM vendor exports when native Python decoders are unavailable."
        ],
    )
