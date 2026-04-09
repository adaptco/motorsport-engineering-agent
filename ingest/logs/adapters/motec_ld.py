"""ingest/logs/adapters/motec_ld module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ingest.logs.types import ParsedLog


def _load_with_ldparser(path: Path) -> Any:
    try:
        import ldparser as module  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised when optional dep missing
        raise RuntimeError(
            "ldparser is required to parse MoTeC .ld files. Install from the upstream repository, or export from MoTeC i2 as CSV/MAT."
        ) from exc

    for candidate in (
        getattr(module, "read_ld_file", None),
        getattr(getattr(module, "ldparser", None), "read_ld_file", None),
    ):
        if callable(candidate):
            return candidate(str(path))
    if hasattr(module, "LogFile"):
        return module.LogFile(str(path))
    raise RuntimeError(
        "Installed ldparser module does not expose a supported read_ld_file / LogFile interface"
    )


def parse_motec_ld(path: Path) -> ParsedLog:
    if path.suffix.lower() == ".ldx":
        raise RuntimeError(
            "MoTeC .ldx is not supported by the selected off-the-shelf parser path; export from i2 as CSV or MAT instead."
        )
    log = _load_with_ldparser(path)
    frame = _to_dataframe(log)
    notes = ["MoTeC .ld parsed with ldparser-compatible interface"]
    return ParsedLog(
        vendor="motec", source_path=path, frame=frame, metadata={"parser": "ldparser"}, notes=notes
    )


def _to_dataframe(log: Any) -> pd.DataFrame:
    channels = getattr(log, "channels", None)
    if isinstance(channels, dict):
        data = {str(key): _extract_series(value) for key, value in channels.items()}
        return pd.DataFrame(data)
    if channels is not None:
        data = {}
        for channel in channels:
            name = getattr(channel, "name", None) or getattr(channel, "Name", None)
            if not name:
                continue
            data[str(name)] = _extract_series(channel)
        if data:
            return pd.DataFrame(data)
    raise RuntimeError("Unable to convert ldparser result into a dataframe")


def _extract_series(value: Any):
    for attr in ("data", "samples", "values"):
        if hasattr(value, attr):
            result = getattr(value, attr)
            return list(result)
    if isinstance(value, (list, tuple)):
        return list(value)
    raise RuntimeError("Unsupported ldparser channel object shape")
