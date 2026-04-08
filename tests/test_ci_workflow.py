from pathlib import Path

import yaml


def _load_workflow(filename: str) -> dict:
    workflow_path = Path(".github/workflows") / filename
    assert workflow_path.exists(), "CI workflow file is missing"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _find_step(steps: list[dict], uses: str) -> dict:
    for step in steps:
        if step.get("uses") == uses:
            return step
    raise AssertionError(f"Step '{uses}' not found in workflow")


def test_mea_kernel_ci_uses_latest_runtime_toolchain() -> None:
    workflow = _load_workflow("ci.yml")

    lint_and_test_job = workflow["jobs"]["lint-and-test"]
    test_job_steps = lint_and_test_job["steps"]

    checkout_step_test = _find_step(test_job_steps, "actions/checkout@v4")
    assert checkout_step_test["uses"] == "actions/checkout@v4"

    setup_python = _find_step(test_job_steps, "actions/setup-python@v4")
    setup_uv = _find_step(test_job_steps, "astral-sh/setup-uv@v3")

    assert setup_python["with"]["python-version"] == "${{ matrix.python-version }}"
    assert setup_uv["uses"] == "astral-sh/setup-uv@v3"
    assert lint_and_test_job["strategy"]["matrix"]["python-version"] == ["3.11", "3.13"]


def test_container_build_workflow_defines_build_images_job() -> None:
    workflow = _load_workflow("container-build.yml")
    build_job_steps = workflow["jobs"]["build-images"]["steps"]

    checkout_step_build = _find_step(build_job_steps, "actions/checkout@v4")
    assert checkout_step_build["uses"] == "actions/checkout@v4"
