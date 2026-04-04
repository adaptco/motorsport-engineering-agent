import json
import re
import tomllib
from pathlib import Path

from control_plane.app import healthz as control_plane_healthz
from mcp_server.app import healthz as mcp_server_healthz


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
    assert match.group("version") == f"{manifest['kernel_version']}.0"
