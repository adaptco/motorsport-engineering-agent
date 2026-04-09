"""tests/test_version_alignment module."""

import json
import re
import tomllib
from pathlib import Path

from control_plane.app import healthz as control_plane_healthz
from mcp_server.app import healthz as mcp_server_healthz
from shared import version as shared_version


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_version_manifest() -> dict[str, object]:
    return json.loads((REPO_ROOT / "VERSION.json").read_text(encoding="utf-8"))


def test_runtime_healthz_matches_version_manifest() -> None:
    manifest = _load_version_manifest()

    expected = {
        "status": "ok",
        "kernel_version": manifest["kernel_version"],
        "package_version": manifest["package_version"],
    }

    assert control_plane_healthz() == expected
    assert mcp_server_healthz() == expected


def test_pyproject_package_version_matches_version_manifest() -> None:
    manifest = _load_version_manifest()
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == manifest["package_version"]


def test_readme_kernel_version_matches_version_manifest() -> None:
    manifest = _load_version_manifest()
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    match = re.search(r"^#\s+MEA Root Kernel v(?P<version>\S+)", readme, flags=re.MULTILINE)
    assert match, "README kernel header not found"
    readme_version = match.group("version")
    kernel_version = str(manifest["kernel_version"])
    assert readme_version == kernel_version or readme_version == f"{kernel_version}.0"


def test_load_version_info_falls_back_when_manifest_missing(tmp_path: Path, monkeypatch) -> None:
    shared_version.load_version_info.cache_clear()
    monkeypatch.setattr(shared_version, "_version_file_path", lambda: tmp_path / "VERSION.json")
    monkeypatch.setattr(shared_version, "package_version", lambda _name: "0.3.4")

    version_info = shared_version.load_version_info()

    assert version_info.package_version == "0.3.4"
    assert version_info.kernel_version == "3.4"
    assert version_info.release_channel == "unknown"
    shared_version.load_version_info.cache_clear()


def test_load_version_info_falls_back_when_manifest_invalid_json(tmp_path: Path, monkeypatch) -> None:
    shared_version.load_version_info.cache_clear()
    broken_manifest = tmp_path / "VERSION.json"
    broken_manifest.write_text("{not-json", encoding="utf-8")

    monkeypatch.setattr(shared_version, "_version_file_path", lambda: broken_manifest)
    monkeypatch.setattr(shared_version, "package_version", lambda _name: "0.5.0")

    version_info = shared_version.load_version_info()

    assert version_info.package_version == "0.5.0"
    assert version_info.kernel_version == "5.0"
    assert version_info.release_channel == "unknown"
    shared_version.load_version_info.cache_clear()


def test_load_version_info_falls_back_when_manifest_missing_fields(tmp_path: Path, monkeypatch) -> None:
    shared_version.load_version_info.cache_clear()
    partial_manifest = tmp_path / "VERSION.json"
    partial_manifest.write_text('{"kernel_version": "3.4"}', encoding="utf-8")

    monkeypatch.setattr(shared_version, "_version_file_path", lambda: partial_manifest)
    monkeypatch.setattr(shared_version, "package_version", lambda _name: "0.5.1")

    version_info = shared_version.load_version_info()

    assert version_info.package_version == "0.5.1"
    assert version_info.kernel_version == "5.1"
    assert version_info.release_channel == "unknown"
    shared_version.load_version_info.cache_clear()
