"""ingest/logs/adapters/iracing_ibt module."""

from __future__ import annotations

from pathlib import Path

from ingest.logs.types import ParsedLog


def parse_iracing_ibt(path: Path) -> ParsedLog:
    try:
        from libibt import ibt  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised when optional dep missing
        raise RuntimeError(
            "libibt is required to parse iRacing .ibt files. Install with: pip install libibt"
        ) from exc

    log = ibt(path)
    table = log.get_channels_as_table()
    frame = table.to_pandas()
    if "timecodes" in frame.columns:
        frame = frame.rename(columns={"timecodes": "timestamp_ms"})
    metadata = dict(getattr(log, "metadata", {}) or {})
    metadata.update({"parser": "libibt", "channel_count": len(getattr(log, "channels", {}))})
    notes = []
    laps = getattr(log, "laps", None)
    if laps is not None and getattr(laps, "num_rows", 0) > 0:
        lap_frame = laps.to_pandas()
        if {"num", "start_time", "end_time"}.issubset(
            lap_frame.columns
        ) and "timestamp_ms" in frame.columns:
            frame["lap_index"] = 0
            for _, lap in lap_frame.iterrows():
                mask = (frame["timestamp_ms"] >= lap["start_time"]) & (
                    frame["timestamp_ms"] < lap["end_time"]
                )
                frame.loc[mask, "lap_index"] = int(lap["num"])
            notes.append("lap_index derived from libibt lap intervals")
    return ParsedLog(
        vendor="iracing", source_path=path, frame=frame, metadata=metadata, notes=notes
    )
