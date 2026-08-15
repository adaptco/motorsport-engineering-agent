"""Regression tests for the repository-owned V3.8 pre-commit policy."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_v38_runtime_references.py"
CONFIG_PATH = ROOT / ".pre-commit-config.yaml"


def _load_checker():
    spec = importlib.util.spec_from_file_location("v38_runtime_reference_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_precommit_configuration_is_parseable_and_wires_the_runtime_guard() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["minimum_pre_commit_version"] == "3.7.0"
    hooks = config["repos"][0]["hooks"]
    hook = next(item for item in hooks if item["id"] == "mea-v38-runtime-reference-guard")
    assert hook["entry"] == "python scripts/check_v38_runtime_references.py"
    assert hook["pass_filenames"] is True


def test_runtime_guard_accepts_v38_pinned_values(tmp_path: Path) -> None:
    candidate = tmp_path / "runtime.yaml"
    candidate.write_text(
        "kernel_version: 3.8\npackage_version: 0.3.8\nimage: mea-worker:3.8\n",
        encoding="utf-8",
    )

    checker = _load_checker()
    assert list(checker._iter_violations(candidate)) == []


def test_runtime_guard_rejects_deprecated_product_versions(tmp_path: Path) -> None:
    candidate = tmp_path / "runtime.yaml"
    candidate.write_text("release: V3." + "7\npackage_version: 0.3." + "7\n", encoding="utf-8")

    checker = _load_checker()
    violations = list(checker._iter_violations(candidate))
    assert len(violations) == 2
    assert all("stale V3.x" in violation for violation in violations)


def test_runtime_guard_rejects_unpinned_mea_image_references(tmp_path: Path) -> None:
    candidate = tmp_path / "runtime.yaml"
    candidate.write_text(
        "image: mea-control-plane:" + "latest\nversion: ${VERSION:-" + "latest}\n",
        encoding="utf-8",
    )

    checker = _load_checker()
    violations = list(checker._iter_violations(candidate))
    assert len(violations) == 2


def test_runtime_guard_ignores_lockfile_content(tmp_path: Path) -> None:
    checker = _load_checker()
    for filename in ("uv.lock", "package-lock.json"):
        lockfile = tmp_path / filename
        lockfile.write_text("version = V3." + "7\n", encoding="utf-8")
        assert list(checker._iter_violations(lockfile)) == []


def test_runtime_guard_allows_external_action_versions(tmp_path: Path) -> None:
    candidate = tmp_path / "workflow.yml"
    candidate.write_text("uses: hadolint/hadolint-action@v3." + "1.0\n", encoding="utf-8")

    checker = _load_checker()
    assert list(checker._iter_violations(candidate)) == []
