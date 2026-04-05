from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ParsedLog:
    vendor: str
    source_path: Path
    frame: pd.DataFrame
    units: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NormalizedArtifacts:
    vendor: str
    input_path: Path
    output_dir: Path
    normalized_csv: Path
    channel_manifest_csv: Path
    session_manifest_json: Path
    row_count: int
    column_count: int
    canonical_columns: list[str]
    notes: list[str] = field(default_factory=list)
