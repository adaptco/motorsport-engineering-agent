from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path


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


LOGGER = logging.getLogger(__name__)


def _fallback_version_info() -> VersionInfo:
    try:
        installed_package_version = package_version("mea-root-kernel")
    except PackageNotFoundError:
        installed_package_version = "0.0.0"

    return VersionInfo(
        kernel_version=_kernel_version_from_package(installed_package_version),
        package_version=installed_package_version,
        release_channel="unknown",
    )


@lru_cache(maxsize=1)
def load_version_info() -> VersionInfo:
    version_file = _version_file_path()
    if not version_file.exists():
        return _fallback_version_info()

    try:
        version_data = json.loads(version_file.read_text(encoding="utf-8"))
        return VersionInfo(
            kernel_version=str(version_data["kernel_version"]),
            package_version=str(version_data["package_version"]),
            release_channel=str(version_data["release_channel"]),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        LOGGER.warning("Failed to load VERSION.json from %s: %s", version_file, exc)
        return _fallback_version_info()
