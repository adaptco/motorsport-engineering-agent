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

    test_job_steps = workflow["jobs"]["test"]["steps"]

    checkout_step_test = _find_step(test_job_steps, "actions/checkout@v6")
    assert checkout_step_test["uses"] == "actions/checkout@v6"

    setup_node = _find_step(test_job_steps, "actions/setup-node@v6")
    setup_python = _find_step(test_job_steps, "actions/setup-python@v6")

    assert str(setup_node["with"]["node-version"]) == "24"
    assert str(setup_python["with"]["python-version"]) == "3.13"


def test_container_build_workflow_defines_build_images_job() -> None:
    workflow = _load_workflow("container-build.yml")
    build_job_steps = workflow["jobs"]["build-images"]["steps"]

    checkout_step_build = _find_step(build_job_steps, "actions/checkout@v4")
    assert checkout_step_build["uses"] == "actions/checkout@v4"


def _load_yaml(path: str) -> dict:
    file_path = Path(path)
    assert file_path.exists(), f"Expected config file is missing: {path}"
    return yaml.safe_load(file_path.read_text(encoding="utf-8"))


def test_deploy_compose_overlays_target_ci_published_image_tags() -> None:
    staging = _load_yaml("deploy/compose/staging.yml")
    production = _load_yaml("deploy/compose/production.yml")

    for compose in (staging, production):
        services = compose["services"]
        assert services["control_plane"]["image"].endswith(":control-plane-${VERSION:-latest}")
        assert services["worker"]["image"].endswith(":worker-${VERSION:-latest}")
        assert services["mcp_server"]["image"].endswith(":mcp-server-${VERSION:-latest}")
        assert "your-org/your-repo" not in services["control_plane"]["image"]
        assert "your-org/your-repo" not in services["worker"]["image"]
        assert "your-org/your-repo" not in services["mcp_server"]["image"]


def test_k8s_manifests_target_ci_published_image_tags() -> None:
    control_plane_manifest = Path("deploy/k8s/control-plane.yaml").read_text(encoding="utf-8")
    worker_manifest = Path("deploy/k8s/worker.yaml").read_text(encoding="utf-8")
    mcp_manifest = Path("deploy/k8s/mcp-server.yaml").read_text(encoding="utf-8")

    assert "${REGISTRY}/${IMAGE_NAME}:control-plane-${VERSION:-latest}" in control_plane_manifest
    assert "${REGISTRY}/${IMAGE_NAME}:worker-${VERSION:-latest}" in worker_manifest
    assert "${REGISTRY}/${IMAGE_NAME}:mcp-server-${VERSION:-latest}" in mcp_manifest
