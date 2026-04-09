"""control_plane/services/job_runner module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


class JobExecutionRequest(BaseModel):
    principal_id: str
    session_id: str
    run_id: str
    trace_id: str
    policy_version: str
    authz_scope: str
    job_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = Field(default=5000, ge=1, le=30000)


class JobExecutionResponse(BaseModel):
    status: str
    job_name: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


def _verify_dir_exists(params: dict[str, Any]) -> list[str]:
    path = Path(str(params["path"]))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"directory_not_found:{path}")
    return ["python", "-c", f"import pathlib; print(pathlib.Path(r'{path}').resolve())"]


def _validate_jsonl_file(params: dict[str, Any]) -> list[str]:
    path = Path(str(params["path"]))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"file_not_found:{path}")
    return ["python", "-c", f"from pathlib import Path; p=Path(r'{path}'); print(p.resolve()); print(p.stat().st_size)"]


ALLOWED_JOBS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "verify_dir_exists": _verify_dir_exists,
    "validate_jsonl_file": _validate_jsonl_file,
}


class JobNotAllowedError(PermissionError):
    pass


def execute_job(request: JobExecutionRequest) -> JobExecutionResponse:
    if request.job_name not in ALLOWED_JOBS:
        raise JobNotAllowedError("job_not_allowed")
    command = ALLOWED_JOBS[request.job_name](request.params)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=request.timeout_ms / 1000,
        check=False,
    )
    return JobExecutionResponse(
        status="complete" if completed.returncode == 0 else "failed",
        job_name=request.job_name,
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
    )
