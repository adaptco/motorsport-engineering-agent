"""tools/cli_iracing_probe module."""


from pathlib import Path
import json
import typer

from ingest.iracing_stream import dump_stream_to_jsonl, stream_iracing_frames
from control_plane.services.replay_service import build_validation_tasks

app = typer.Typer(help="Capture direct iRacing stream to JSONL and print validation metrics")


@app.command()
def probe(
    out_path: str,
    max_frames: int = 600,
    sampling_hz: int = 60,
):
    channel_map = {"Throttle": "Throttle", "Brake": "Brake", "Speed": "Speed"}
    metrics = dump_stream_to_jsonl(
        stream_iracing_frames(channel_map=channel_map, sampling_hz=sampling_hz),
        Path(out_path),
        max_frames=max_frames,
    )
    tasks = build_validation_tasks(metrics, sampling_hz)
    typer.echo(json.dumps({
        "metrics": metrics.model_dump(),
        "tasks": [task.model_dump() for task in tasks],
    }, indent=2))


if __name__ == "__main__":
    app()
