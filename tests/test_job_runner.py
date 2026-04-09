"""tests/test_job_runner module."""

from pathlib import Path

import pytest

from control_plane.services.job_runner import JobExecutionRequest, JobNotAllowedError, execute_job


def test_execute_job_allows_named_job_only(tmp_path: Path):
    request = JobExecutionRequest(
        principal_id="agent_01",
        session_id="session-1",
        run_id="run-1",
        trace_id="trace-1",
        policy_version="rbac.v1",
        authz_scope="read-only",
        job_name="verify_dir_exists",
        params={"path": str(tmp_path)},
    )
    result = execute_job(request)
    assert result.status == "complete"
    assert str(tmp_path.resolve()) in result.stdout


def test_execute_job_rejects_unknown_job():
    request = JobExecutionRequest(
        principal_id="agent_01",
        session_id="session-1",
        run_id="run-1",
        trace_id="trace-1",
        policy_version="rbac.v1",
        authz_scope="read-only",
        job_name="rm_rf_everything",
        params={},
    )
    with pytest.raises(JobNotAllowedError):
        execute_job(request)
