from pathlib import Path

import yaml


def _load_ci_workflow() -> dict:
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.exists(), "CI workflow file is missing"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _find_step(steps: list[dict], uses: str) -> dict:
    for step in steps:
        if step.get("uses") == uses:
            return step
    raise AssertionError(f"Step '{uses}' not found in workflow")


def test_mea_kernel_ci_uses_latest_runtime_toolchain() -> None:
    workflow = _load_ci_workflow()

    test_job_steps = workflow["jobs"]["test"]["steps"]
    build_job_steps = workflow["jobs"]["build-images"]["steps"]

    checkout_step_test = _find_step(test_job_steps, "actions/checkout@v6")
    checkout_step_build = _find_step(build_job_steps, "actions/checkout@v6")
    assert checkout_step_test["uses"] == "actions/checkout@v6"
    assert checkout_step_build["uses"] == "actions/checkout@v6"

    setup_node = _find_step(test_job_steps, "actions/setup-node@v6")
    setup_python = _find_step(test_job_steps, "actions/setup-python@v6")

    assert str(setup_node["with"]["node-version"]) == "24"
    assert str(setup_python["with"]["python-version"]) == "3.13"
