"""shared/version module."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

logger = logging.getLogger(__name__)

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


@lru_cache(maxsize=1)
def load_version_info() -> VersionInfo:
    version_file = _version_file_path()
    if version_file.exists():
        try:
            version_data = json.loads(version_file.read_text(encoding="utf-8"))
            return VersionInfo(
                kernel_version=version_data["kernel_version"],
                package_version=version_data["package_version"],
                release_channel=version_data["release_channel"],
            )
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.warning(f"Failed to load VERSION.json: {e}. Falling back to package metadata.")

    try:
        installed_package_version = package_version("mea-root-kernel")
    except PackageNotFoundError:
        installed_package_version = "0.0.0"

    return VersionInfo(
        kernel_version=_kernel_version_from_package(installed_package_version),
        package_version=installed_package_version,
        release_channel="unknown",
    )
