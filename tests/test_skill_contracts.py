"""Regression tests for the V3.8 governed SKILL.md contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.skill_contracts import (
    SkillContractError,
    parse_skill_contract,
    validate_skill_repository,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _write_skill(root: Path, relative_path: str, metadata: str) -> Path:
    path = root / relative_path / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{metadata}\n---\n\n# Skill\n", encoding="utf-8")
    return path


def test_repository_skills_have_governed_v38_contracts() -> None:
    contracts = validate_skill_repository(REPOSITORY_ROOT)

    assert len(contracts) >= 7
    assert {contract.contract_version for contract in contracts} == {"1.0"}
    assert all(contract.policy_scope for contract in contracts)


def test_skill_contract_rejects_missing_required_metadata(tmp_path: Path) -> None:
    path = _write_skill(
        tmp_path,
        "missing-contract-version",
        "name: missing-contract-version\ndescription: This skill intentionally omits required version metadata.",
    )

    with pytest.raises(SkillContractError, match="contract_version"):
        parse_skill_contract(path, repository_root=tmp_path)


def test_skill_contract_rejects_source_outside_repository(tmp_path: Path) -> None:
    path = _write_skill(
        tmp_path,
        "unsafe-source",
        "\n".join(
            [
                "name: unsafe-source",
                "description: This skill intentionally attempts to reference a path outside the repository.",
                'contract_version: "1.0"',
                "source_of_truth:",
                "  - ../outside.md",
            ]
        ),
    )

    with pytest.raises(SkillContractError, match="escapes repository root"):
        parse_skill_contract(path, repository_root=tmp_path)


def test_skill_repository_rejects_duplicate_capability_names(tmp_path: Path) -> None:
    metadata = "\n".join(
        [
            "name: duplicate-skill",
            "description: This is a valid skill metadata block used to prove duplicate rejection.",
            'contract_version: "1.0"',
            "policy_scope: read",
        ]
    )
    _write_skill(tmp_path, "one", metadata)
    _write_skill(tmp_path, "two", metadata)

    with pytest.raises(SkillContractError, match="duplicate governed skill names"):
        validate_skill_repository(tmp_path)
