"""ingest/logs/util module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def coerce_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        try:
            result[column] = pd.to_numeric(result[column])
        except Exception:
            pass
    return result


def infer_delimiter(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sample = "\n".join(text.splitlines()[:5])
    if ";" in sample and sample.count(";") >= sample.count(","):
        return ";"
    if "\t" in sample:
        return "\t"
    return None


def flatten_mat_dict(raw: dict[str, Any]) -> pd.DataFrame:
    series: dict[str, Any] = {}
    expected_len: int | None = None
    for key, value in raw.items():
        if key.startswith("__"):
            continue
        if hasattr(value, "shape"):
            flat = value.ravel()
            if flat.ndim == 1 and flat.size > 1:
                if expected_len is None:
                    expected_len = int(flat.size)
                if flat.size == expected_len:
                    series[key] = flat
    if not series:
        raise ValueError("MAT file does not contain any 1D telemetry arrays with shared length")
    return pd.DataFrame(series)
