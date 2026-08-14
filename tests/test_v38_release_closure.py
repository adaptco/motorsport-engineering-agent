"""Release-closure regression tests for the sole supported V3.8 baseline."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEGACY_KERNEL_REFERENCE = re.compile(r"(?i)\bv3\.(?:[0-7])(?:\.\d+)?\b")
LEGACY_PACKAGE_REFERENCE = re.compile(r"\b0\.3\.(?:[0-7])(?:\.\d+)?\b")


def test_v38_release_manifest_is_canonical_and_points_to_existing_artifacts() -> None:
    manifest = json.loads((ROOT / "release" / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))

    assert manifest["kernel_version"] == "3.8"
    assert manifest["package_version"] == "0.3.8"
    assert manifest["release_channel"] == "stable"
    assert (ROOT / manifest["runtime_contract"]).is_file()
    assert (ROOT / manifest["skill_contract"]).is_file()
    assert (ROOT / manifest["reliability_policy"]).is_file()
    assert (ROOT / manifest["deployment"]["compose"]).is_file()
    assert (ROOT / manifest["deployment"]["container"]).is_file()
    assert (ROOT / manifest["deployment"]["verification"]).is_file()


def test_v38_release_docs_do_not_carry_deprecated_product_versions() -> None:
    active_paths = [
        ROOT / "README.md",
        ROOT / "PRD.md",
        ROOT / "PROGRESS.md",
        ROOT / "CHANGELOG.md",
        ROOT / "TASK_LEDGER.md",
        ROOT / "release",
        ROOT / "deploy",
        ROOT / "docs" / "ops",
        ROOT / "docs" / "V38_RELEASE_GUIDE.md",
        ROOT / "docs" / "system_architecture.md",
        ROOT / "docs" / "versioning-spec.md",
    ]
    files: list[Path] = []
    for path in active_paths:
        files.extend([path] if path.is_file() else path.rglob("*"))

    for path in files:
        if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml", ".sh"}:
            continue
        content = path.read_text(encoding="utf-8")
        assert not LEGACY_KERNEL_REFERENCE.search(content), path
        assert not LEGACY_PACKAGE_REFERENCE.search(content), path


def test_v38_hosting_blueprint_has_no_dead_compiled_workflow_path() -> None:
    render_blueprint = (ROOT / "infra" / "render.yaml").read_text(encoding="utf-8")

    assert "MEA_COMPILED_WORKFLOW_PLAN_PATH" not in render_blueprint
    assert "configs/compiled_workflow_plan.yaml" not in render_blueprint
    assert yaml.safe_load(render_blueprint)
