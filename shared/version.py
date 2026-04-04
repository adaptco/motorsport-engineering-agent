from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class VersionInfo:
    kernel_version: str
    package_version: str
    release_channel: str


def _version_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / "VERSION.json"


@lru_cache(maxsize=1)
def load_version_info() -> VersionInfo:
    version_data = json.loads(_version_file_path().read_text(encoding="utf-8"))
    return VersionInfo(
        kernel_version=version_data["kernel_version"],
        package_version=version_data["package_version"],
        release_channel=version_data["release_channel"],
    )
