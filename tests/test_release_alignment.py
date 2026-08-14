"""Regression checks for active V3.8 release surfaces."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v38_release_metadata_is_consistent() -> None:
    version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert version["kernel_version"] == "3.8"
    assert version["package_version"] == "0.3.8"
    assert pyproject["project"]["version"] == "0.3.8"
    assert (ROOT / ".git-commit-sha").read_text(encoding="utf-8").strip().startswith("v3.8")


def test_v38_deployment_artifacts_replace_active_v36_paths() -> None:
    compose_v38 = ROOT / "deploy" / "compose" / "docker-compose.v3.8.yml"
    container_v38 = ROOT / "deploy" / "containers" / "mea-v3.8" / "Dockerfile"
    verification_v38 = ROOT / "deploy" / "verify-v3.8.sh"

    assert compose_v38.is_file()
    assert container_v38.is_file()
    assert verification_v38.is_file()
    assert not (ROOT / "deploy" / "compose" / "docker-compose.v3.6.yml").exists()
    assert not (ROOT / "deploy" / "containers" / "mea-v3.6").exists()
    assert not (ROOT / "deploy" / "verify-v3.6.sh").exists()

    assert 'MEA_VERSION: "3.8"' in compose_v38.read_text(encoding="utf-8")
    assert 'MEA_KERNEL_VERSION: "3.8"' in compose_v38.read_text(encoding="utf-8")
    container_content = container_v38.read_text(encoding="utf-8")
    assert "as v3.8-control-plane" in container_content
    assert "COPY pyproject.toml uv.lock ./" in container_content
    assert "uv sync --frozen" in container_content
    assert "expected 3.8" in verification_v38.read_text(encoding="utf-8")


def test_active_release_docs_and_automation_target_v38() -> None:
    active_files = [
        ROOT / ".github" / "workflows" / "deploy.yml",
        ROOT / "contracts" / "runtime" / "README.md",
        ROOT / "deploy" / "README.md",
        ROOT / "deploy" / "deploy.sh",
        ROOT / "infra" / "render.yaml",
        ROOT / "scripts" / "github_pr_lifecycle.sh",
    ]
    for path in active_files:
        content = path.read_text(encoding="utf-8")
        assert "v3.6" not in content.lower(), path
        assert "0.3.6" not in content, path

    deploy_readme = (ROOT / "deploy" / "README.md").read_text(encoding="utf-8")
    assert "[PRD.md](../PRD.md)" in deploy_readme
    assert "[VERSION.json](../VERSION.json)" in deploy_readme
