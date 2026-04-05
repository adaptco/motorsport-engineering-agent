from pathlib import Path
import re

import yaml


def _load_ci_workflow() -> dict:
    workflow_path = Path(".github/workflows/ci.yml")
    assert workflow_path.exists(), "CI workflow file is missing"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _find_step_for_action(steps: list[dict], action: str) -> dict:
    for step in steps:
        uses = step.get("uses")
        if isinstance(uses, str) and uses.startswith(f"{action}@"):
            return step
    raise AssertionError(f"Step for '{action}' not found in workflow")


def _action_major_version(step: dict) -> int:
    uses = step.get("uses")
    assert isinstance(uses, str), "Workflow step is missing a valid 'uses' value"
    match = re.search(r"@v(\d+)$", uses)
    assert match, f"Unable to parse action major version from '{uses}'"
    return int(match.group(1))


def test_mea_kernel_ci_uses_latest_runtime_toolchain() -> None:
    workflow = _load_ci_workflow()

    test_job_steps = workflow["jobs"]["test"]["steps"]
    build_job_steps = workflow["jobs"]["build-images"]["steps"]

    checkout_step_test = _find_step_for_action(test_job_steps, "actions/checkout")
    checkout_step_build = _find_step_for_action(build_job_steps, "actions/checkout")
    checkout_major_test = _action_major_version(checkout_step_test)
    checkout_major_build = _action_major_version(checkout_step_build)
    assert checkout_major_test >= 4
    assert checkout_major_build == checkout_major_test

    setup_node = _find_step_for_action(test_job_steps, "actions/setup-node")
    setup_python = _find_step_for_action(test_job_steps, "actions/setup-python")
    assert _action_major_version(setup_node) >= 6
    assert _action_major_version(setup_python) >= 5

    assert str(setup_node["with"]["node-version"]) == "24"
    assert str(setup_python["with"]["python-version"]) == "3.13"
