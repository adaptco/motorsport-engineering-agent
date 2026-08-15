"""Regression coverage for the V3.8 runtime-reference audit."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
V38_IMAGES = {
    "k8s/control-plane-deployment.yaml": "mea-control-plane:3.8",
    "k8s/worker-deployment.yaml": "mea-worker:3.8",
    "k8s/mcp-server-deployment.yaml": "mea-mcp-server:3.8",
}
UNPINNED_TAG = ":" + "latest"
UNPINNED_VERSION_FALLBACK = "${VERSION:-" + "latest}"

DOCKER_GUIDES = (
    "DOCKER_CONSOLIDATION_CHECKLIST.md",
    "DOCKER_CONSOLIDATION_SUMMARY.md",
    "DOCKER_CONTAINERIZATION.md",
    "DOCKER_OPTIMIZATION_REPORT.md",
    "DOCKER_QUICK_REFERENCE.md",
    "GITHUB_ACTIONS_DOCKER_SETUP.md",
    "k8s/README.md",
)


def _text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_mcp_runtime_contract_is_versioned_for_v38_and_validates_against_its_schema() -> None:
    config = json.loads(_text("mcp.json"))
    schema_path = ROOT / config["$schema"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert config["version"] == "3.8"
    assert config["package_version"] == "0.3.8"
    jsonschema.validate(config, schema)


def test_kubernetes_manifests_pin_v38_component_images_and_release_label() -> None:
    kustomization = yaml.safe_load(_text("k8s/kustomization.yaml"))

    assert kustomization["commonLabels"]["app.kubernetes.io/version"] == "3.8"
    for relative_path, expected_image in V38_IMAGES.items():
        manifest = yaml.safe_load(_text(relative_path))
        image = manifest["spec"]["template"]["spec"]["containers"][0]["image"]
        assert image == expected_image
        assert UNPINNED_TAG not in image


def test_documented_runtime_paths_use_pinned_v38_images() -> None:
    for relative_path in DOCKER_GUIDES:
        text = _text(relative_path)
        assert "mea-root-kernel" + UNPINNED_TAG not in text
        assert "mea-control-plane" + UNPINNED_TAG not in text
        assert "mea-worker" + UNPINNED_TAG not in text
        assert "mea-mcp-server" + UNPINNED_TAG not in text

    assert "VERSION ?= 3.8" in _text("Makefile")
    assert "KERNEL_VERSION=3.8" in _text(".env.example")
    assert "PACKAGE_VERSION=0.3.8" in _text(".env.example")
    for relative_path in (
        "deploy/k8s/control-plane.yaml",
        "deploy/k8s/worker.yaml",
        "deploy/k8s/mcp-server.yaml",
    ):
        text = _text(relative_path)
        assert UNPINNED_VERSION_FALLBACK not in text
        assert "${VERSION:-3.8}" in text
        assert 'version: "3.8"' in text

    assert "mea-mcp-server:3.8" in _text(".github/workflows/trivy.yml")
    assert "mea-sbom:3.8" in _text(".github/workflows/container-build.yml")


def test_stale_kernel_examples_are_removed_from_architecture_documents() -> None:
    for relative_path in (
        "docs/control_plane_architecture.md",
        "docs/mcp-server-implementation-analysis.md",
    ):
        text = _text(relative_path)
        for legacy_version in ("3" + ".3", "3" + ".2"):
            assert f'"kernel_version": "{legacy_version}"' not in text
        assert '"kernel_version": "3.8"' in text
        assert '"package_version": "0.3.8"' in text


def test_v38_deployment_and_workflow_yamls_remain_parseable() -> None:
    yaml_paths = (
        ".github/workflows/container-build.yml",
        ".github/workflows/trivy.yml",
        "deploy/compose/staging.yml",
        "deploy/compose/production.yml",
        "deploy/k8s/control-plane.yaml",
        "deploy/k8s/worker.yaml",
        "deploy/k8s/mcp-server.yaml",
        "k8s/kustomization.yaml",
        "k8s/control-plane-deployment.yaml",
        "k8s/worker-deployment.yaml",
        "k8s/mcp-server-deployment.yaml",
    )
    for relative_path in yaml_paths:
        documents = list(yaml.safe_load_all(_text(relative_path)))
        assert documents and all(document is not None for document in documents), relative_path
