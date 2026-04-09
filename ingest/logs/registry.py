"""ingest/logs/registry module."""

from __future__ import annotations

from pathlib import Path

from ingest.logs.adapters import (
    parse_aim_xrk,
    parse_csv_export,
    parse_iracing_ibt,
    parse_motec_ld,
    parse_pi_mat,
    parse_vbox_vbo,
)
from ingest.logs.canonical import SUPPORTED_SOURCE_EXTENSIONS
from ingest.logs.normalizer import normalize_log
from ingest.logs.types import NormalizedArtifacts


SUPPORTED_SOURCES = tuple(SUPPORTED_SOURCE_EXTENSIONS.keys())


def detect_source(path: str | Path, vendor_hint: str | None = None) -> str:
    path = Path(path)
    if vendor_hint:
        vendor = vendor_hint.lower()
        if vendor not in SUPPORTED_SOURCES:
            raise ValueError(f"Unsupported vendor hint: {vendor_hint}")
        return vendor
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return "csv_export"
    for vendor, suffixes in SUPPORTED_SOURCE_EXTENSIONS.items():
        if suffix in suffixes:
            if vendor == "csv_export":
                return "csv_export"
            return vendor
    raise ValueError(f"Unsupported file extension: {suffix}")


def parser_statuses() -> list[dict[str, object]]:
    statuses = []
    module_checks = {
        "motec": "ldparser",
        "iracing": "libibt",
        "aim": "libxrk",
        "vbox": None,
        "pi": None,
        "haltech": None,
        "aem": None,
        "csv_export": None,
    }
    notes = {
        "motec": "Native .ld via ldparser; export .ldx from i2 as CSV/MAT fallback.",
        "iracing": "Native .ibt via libibt.",
        "aim": "Native .xrk/.xrz via libxrk.",
        "vbox": "Native .vbo via text parser.",
        "pi": "Use Pi Toolbox MAT export by default; direct .pds support is not included in this kernel patch.",
        "haltech": "Use official CSV/TXT export from ESP/NSP and ingest via generic CSV adapter.",
        "aem": "Use exported CSV/TXT and ingest via generic CSV adapter.",
        "csv_export": "Generic CSV/TXT export adapter.",
    }
    for vendor in SUPPORTED_SOURCES:
        module_name = module_checks[vendor]
        available = True
        if module_name:
            try:
                __import__(module_name)
            except Exception:
                available = False
        statuses.append(
            {
                "vendor": vendor,
                "native_extensions": list(SUPPORTED_SOURCE_EXTENSIONS[vendor]),
                "parser_module": module_name,
                "available": available,
                "notes": notes[vendor],
            }
        )
    return statuses


def normalize_log_file(input_path: str | Path, output_dir: str | Path, vendor_hint: str | None = None, session_id: str | None = None) -> NormalizedArtifacts:
    path = Path(input_path)
    source = detect_source(path, vendor_hint=vendor_hint)
    if source == "motec":
        parsed = parse_motec_ld(path)
    elif source == "iracing":
        parsed = parse_iracing_ibt(path)
    elif source == "aim":
        parsed = parse_aim_xrk(path)
    elif source == "vbox":
        parsed = parse_vbox_vbo(path)
    elif source == "pi":
        parsed = parse_pi_mat(path)
    elif source == "haltech":
        parsed = parse_csv_export(path, vendor="haltech")
    elif source == "aem":
        parsed = parse_csv_export(path, vendor="aem")
    else:
        parsed = parse_csv_export(path, vendor="csv_export")
    return normalize_log(parsed, Path(output_dir), session_id=session_id)
