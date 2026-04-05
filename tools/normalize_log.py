from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingest.logs import normalize_log_file, parser_statuses  # noqa: E402

app = typer.Typer(help="Normalize native motorsport telemetry log files into canonical CSV artifacts.")


@app.command("sources")
def sources() -> None:
    typer.echo(json.dumps(parser_statuses(), indent=2))


@app.command("run")
def run(
    input_path: Path = typer.Option(..., "--input", exists=True, readable=True, help="Native source log file or exported CSV/MAT file"),
    output_dir: Path = typer.Option(..., "--out", file_okay=False, dir_okay=True, help="Directory for normalized CSV artifacts"),
    vendor: str | None = typer.Option(None, "--vendor", help="Optional vendor override: motec, iracing, aim, vbox, pi, haltech, aem, csv_export"),
    session_id: str | None = typer.Option(None, "--session-id", help="Optional session identifier override"),
) -> None:
    artifacts = normalize_log_file(input_path=input_path, output_dir=output_dir, vendor_hint=vendor, session_id=session_id)
    typer.echo(
        json.dumps(
            {
                "status": "complete",
                "vendor": artifacts.vendor,
                "input_path": str(artifacts.input_path),
                "output_dir": str(artifacts.output_dir),
                "normalized_csv": str(artifacts.normalized_csv),
                "channel_manifest_csv": str(artifacts.channel_manifest_csv),
                "session_manifest_json": str(artifacts.session_manifest_json),
                "row_count": artifacts.row_count,
                "column_count": artifacts.column_count,
                "canonical_columns": artifacts.canonical_columns,
                "notes": artifacts.notes,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
