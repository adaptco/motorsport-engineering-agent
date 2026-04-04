from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VersionInfo:
    kernel_version: str
    package_version: str
    release_channel: str


def _version_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / "VERSION.json"


def _kernel_version_from_package(package: str) -> str:
    parts = package.split(".")
    if len(parts) < 3:
        return package
    major, minor, patch = parts[:3]
    if major == "0":
        return f"{minor}.{patch}"
    return f"{major}.{minor}"


def _coerce_manifest_version_info(version_data: dict[str, Any]) -> VersionInfo | None:
    kernel_version = version_data.get("kernel_version")
    package_ver = version_data.get("package_version")
    release_channel = version_data.get("release_channel")

    if not isinstance(kernel_version, str):
        return None
    if not isinstance(package_ver, str):
        return None
    if not isinstance(release_channel, str):
        return None

    return VersionInfo(
        kernel_version=kernel_version,
        package_version=package_ver,
        release_channel=release_channel,
    )


@lru_cache(maxsize=1)
def load_version_info() -> VersionInfo:
    version_file = _version_file_path()
    if version_file.exists():
        try:
            version_data = json.loads(version_file.read_text(encoding="utf-8"))
            if isinstance(version_data, dict):
                manifest_info = _coerce_manifest_version_info(version_data)
                if manifest_info is not None:
                    return manifest_info
        except (OSError, json.JSONDecodeError):
            pass

    try:
        installed_package_version = package_version("mea-root-kernel")
    except PackageNotFoundError:
        installed_package_version = "0.0.0"

    return VersionInfo(
        kernel_version=_kernel_version_from_package(installed_package_version),
        package_version=installed_package_version,
        release_channel="unknown",
    )
