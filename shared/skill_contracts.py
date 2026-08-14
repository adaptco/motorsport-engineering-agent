"""Validation helpers for governed V3.8 ``SKILL.md`` capabilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class SkillContractError(ValueError):
    """Raised when a governed skill does not satisfy the repository contract."""


@dataclass(frozen=True)
class SkillContract:
    """Validated metadata for one governed skill capability."""

    name: str
    description: str
    contract_version: str
    policy_scope: str | None
    source_of_truth: tuple[str, ...]
    path: Path


@lru_cache(maxsize=1)
def _skill_contract_validator() -> Draft202012Validator:
    schema_path = (
        Path(__file__).resolve().parents[1] / "contracts" / "skills" / "skill_contract.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _front_matter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillContractError(f"{path}: expected YAML front matter starting on line 1")

    try:
        end_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise SkillContractError(f"{path}: expected YAML front matter terminator") from exc

    metadata = yaml.safe_load("\n".join(lines[1:end_index]))
    if not isinstance(metadata, dict):
        raise SkillContractError(f"{path}: YAML front matter must be a mapping")
    return metadata


def parse_skill_contract(path: Path, *, repository_root: Path | None = None) -> SkillContract:
    """Parse and validate one SKILL.md metadata block against the V3.8 schema."""

    metadata = _front_matter(path)
    errors = sorted(
        _skill_contract_validator().iter_errors(metadata), key=lambda error: list(error.path)
    )
    if errors:
        details = "; ".join(error.message for error in errors)
        raise SkillContractError(f"{path}: invalid governed skill metadata: {details}")

    root = (repository_root or Path(__file__).resolve().parents[1]).resolve()
    source_of_truth = tuple(str(item) for item in metadata.get("source_of_truth", []))
    for source_path in source_of_truth:
        candidate = (root / source_path).resolve()
        if root not in candidate.parents and candidate != root:
            raise SkillContractError(
                f"{path}: source_of_truth escapes repository root: {source_path}"
            )
        if not candidate.exists():
            raise SkillContractError(f"{path}: source_of_truth does not exist: {source_path}")

    return SkillContract(
        name=str(metadata["name"]),
        description=str(metadata["description"]),
        contract_version=str(metadata["contract_version"]),
        policy_scope=(str(metadata["policy_scope"]) if "policy_scope" in metadata else None),
        source_of_truth=source_of_truth,
        path=path,
    )


def validate_skill_repository(repository_root: Path | None = None) -> list[SkillContract]:
    """Validate every governed SKILL.md and enforce unique capability identities."""

    root = (repository_root or Path(__file__).resolve().parents[1]).resolve()
    ignored_directories = {".git", ".venv", "node_modules", "__pycache__"}
    skill_paths = sorted(
        path
        for path in root.rglob("SKILL.md")
        if not any(part in ignored_directories for part in path.relative_to(root).parts)
    )
    if not skill_paths:
        raise SkillContractError(f"{root}: no governed SKILL.md files found")

    contracts = [parse_skill_contract(path, repository_root=root) for path in skill_paths]
    names = [contract.name for contract in contracts]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        raise SkillContractError(
            f"{root}: duplicate governed skill names: {', '.join(duplicate_names)}"
        )
    return contracts
