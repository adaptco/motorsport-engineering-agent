
from pathlib import Path
import typer

from control_plane.services.replay_service import replay_artifact
from shared.models import ReplayRequest

app = typer.Typer(help="Validate telemetry JSONL artifacts for deterministic replay")


@app.command()
def validate(
    artifact_path: str,
    sampling_hz: int = 60,
    max_frames: int | None = None,
):
    response = replay_artifact(
        ReplayRequest(artifact_path=artifact_path, sampling_hz=sampling_hz, max_frames=max_frames)
    )
    typer.echo(response.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
