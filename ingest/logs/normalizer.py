"""ingest/logs/normalizer module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ingest.logs.canonical import CANONICAL_CHANNELS
from ingest.logs.types import NormalizedArtifacts, ParsedLog


def normalize_log(parsed: ParsedLog, output_dir: Path, session_id: str | None = None) -> NormalizedArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = parsed.frame.copy()
    source.columns = [str(column).strip() for column in source.columns]
    normalized = pd.DataFrame()
    manifest_rows: list[dict[str, Any]] = []

    for spec in CANONICAL_CHANNELS:
        source_column = _find_source_column(source, spec.aliases)
        if source_column is None:
            continue
        series = source[source_column]
        converted = _convert_series(series, canonical=spec.canonical, source_column=source_column, unit_in=parsed.units.get(source_column))
        normalized[spec.canonical] = converted
        manifest_rows.append(
            {
                "source_vendor": parsed.vendor,
                "source_file": parsed.source_path.name,
                "source_channel": source_column,
                "canonical_channel": spec.canonical,
                "unit_in": parsed.units.get(source_column, ""),
                "unit_out": spec.unit_out,
                "notes": "; ".join(parsed.notes),
            }
        )

    if "timestamp_ms" not in normalized.columns:
        normalized.insert(0, "timestamp_ms", range(0, len(source)))
        manifest_rows.append(
            {
                "source_vendor": parsed.vendor,
                "source_file": parsed.source_path.name,
                "source_channel": "generated_index",
                "canonical_channel": "timestamp_ms",
                "unit_in": "index",
                "unit_out": "ms",
                "notes": "Generated synthetic monotonic timebase because no timestamp channel was found.",
            }
        )
        parsed.notes.append("timestamp_ms generated from row index")

    normalized.insert(1, "source_vendor", parsed.vendor)
    normalized.insert(2, "session_id", session_id or parsed.metadata.get("session_id") or parsed.source_path.stem)

    normalized_csv = output_dir / "normalized_channels.csv"
    manifest_csv = output_dir / "channel_manifest.csv"
    session_json = output_dir / "session_manifest.json"

    normalized.to_csv(normalized_csv, index=False)
    pd.DataFrame(manifest_rows).to_csv(manifest_csv, index=False)

    session_manifest = {
        "source_vendor": parsed.vendor,
        "source_file": str(parsed.source_path),
        "native_format": parsed.source_path.suffix.lower(),
        "rows": int(len(normalized)),
        "columns": list(normalized.columns),
        "canonical_columns": [column for column in normalized.columns if column not in {"source_vendor", "session_id"}],
        "notes": parsed.notes,
        "metadata": parsed.metadata,
    }
    session_json.write_text(json.dumps(session_manifest, indent=2), encoding="utf-8")

    return NormalizedArtifacts(
        vendor=parsed.vendor,
        input_path=parsed.source_path,
        output_dir=output_dir,
        normalized_csv=normalized_csv,
        channel_manifest_csv=manifest_csv,
        session_manifest_json=session_json,
        row_count=int(len(normalized)),
        column_count=int(len(normalized.columns)),
        canonical_columns=list(normalized.columns),
        notes=list(parsed.notes),
    )


def _find_source_column(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    lower_map = {column.lower(): column for column in frame.columns}
    for alias in aliases:
        match = lower_map.get(alias.lower())
        if match is not None:
            return match
    return None


def _convert_series(series: pd.Series, canonical: str, source_column: str, unit_in: str | None) -> pd.Series:
    working = pd.to_numeric(series, errors="coerce")
    unit = (unit_in or "").lower()
    name = source_column.lower()

    if canonical == "timestamp_ms":
        if "sec" in unit or name in {"time", "seconds"}:
            return working * 1000.0
        return working
    if canonical == "speed_mps":
        if "km/h" in unit or "kmh" in unit or "velocity kmh" in name or name.endswith("kmh"):
            return working / 3.6
        return working
    if canonical in {"throttle_pct", "brake_pct"}:
        if "bar" in unit and canonical == "brake_pct":
            clipped = working.clip(lower=0)
            max_value = clipped.max() or 1
            return (clipped / max_value) * 100.0
        return working
    return working
