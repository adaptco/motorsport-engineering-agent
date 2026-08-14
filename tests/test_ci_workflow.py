"""tests/test_ci_workflow module."""

from pathlib import Path
from typing import Any, cast

import yaml


def _load_workflow(filename: str) -> dict[str, Any]:
    workflow_path = Path(".github/workflows") / filename
    assert workflow_path.exists(), "CI workflow file is missing"
    return cast(dict[str, Any], yaml.safe_load(workflow_path.read_text(encoding="utf-8")))


def _find_step(steps: list[dict[str, Any]], uses: str) -> dict[str, Any]:
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


def _load_yaml(path: str) -> dict[str, Any]:
    file_path = Path(path)
    assert file_path.exists(), f"Expected config file is missing: {path}"
    return cast(dict[str, Any], yaml.safe_load(file_path.read_text(encoding="utf-8")))


def test_deploy_compose_overlays_target_ci_published_image_tags() -> None:
    staging = _load_yaml("deploy/compose/staging.yml")
    production = _load_yaml("deploy/compose/production.yml")

    for compose in (staging, production):
        services = compose["services"]
        assert services["control_plane"]["image"].endswith(":control-plane-${VERSION:-3.8}")
        assert services["worker"]["image"].endswith(":worker-${VERSION:-3.8}")
        assert services["mcp_server"]["image"].endswith(":mcp-server-${VERSION:-3.8}")
        assert "your-org/your-repo" not in services["control_plane"]["image"]
        assert "your-org/your-repo" not in services["worker"]["image"]
        assert "your-org/your-repo" not in services["mcp_server"]["image"]


def test_k8s_manifests_target_ci_published_image_tags() -> None:
    control_plane_manifest = Path("deploy/k8s/control-plane.yaml").read_text(encoding="utf-8")
    worker_manifest = Path("deploy/k8s/worker.yaml").read_text(encoding="utf-8")
    mcp_manifest = Path("deploy/k8s/mcp-server.yaml").read_text(encoding="utf-8")

    assert "${REGISTRY}/${IMAGE_NAME}:control-plane-${VERSION:-3.8}" in control_plane_manifest
    assert "${REGISTRY}/${IMAGE_NAME}:worker-${VERSION:-3.8}" in worker_manifest
    assert "${REGISTRY}/${IMAGE_NAME}:mcp-server-${VERSION:-3.8}" in mcp_manifest
