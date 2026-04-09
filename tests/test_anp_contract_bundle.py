"""tests/test_anp_contract_bundle module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parent.parent
ANP_SCHEMA_DIR = REPO_ROOT / "contracts" / "anp" / "schemas"
ANP_EXAMPLE_DIR = REPO_ROOT / "contracts" / "anp" / "examples"
AXP_SCHEMA_PATH = REPO_ROOT / "contracts" / "axp" / "schemas" / "axp-core-foundation.bundle.schema.json"
AXP_DICTIONARY_PATH = REPO_ROOT / "contracts" / "axp" / "dictionaries" / "canonical-token-dictionary.json"

SCHEMA_EXAMPLE_PAIRS = [
    ("anp-route-decision.schema.json", "anp-route-decision.example.json"),
    ("acp-handoff-envelope.schema.json", "acp-handoff-envelope.example.json"),
    ("workflow-cursor.schema.json", "workflow-cursor.example.json"),
    ("acp-execution-receipt.schema.json", "acp-execution-receipt.example.json"),
    ("acp-commit-receipt.schema.json", "acp-commit-receipt.example.json"),
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_registry() -> Registry:
    registry = Registry()
    for schema_path in ANP_SCHEMA_DIR.glob("*.json"):
        schema = _read_json(schema_path)
        resource = Resource.from_contents(schema)
        schema_id = schema.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, resource)
        registry = registry.with_resource(schema_path.name, resource)
    return registry


@pytest.fixture(scope="session")
def schema_registry() -> Registry:
    # Shared registry avoids rebuilding schema resources for each parametrized case.
    return _schema_registry()


def test_anp_bundle_files_exist() -> None:
    for schema_name, example_name in SCHEMA_EXAMPLE_PAIRS:
        assert (ANP_SCHEMA_DIR / schema_name).is_file(), f"missing schema: {schema_name}"
        assert (ANP_EXAMPLE_DIR / example_name).is_file(), f"missing example: {example_name}"

    assert AXP_SCHEMA_PATH.is_file(), "missing AXP foundation schema bundle"
    assert AXP_DICTIONARY_PATH.is_file(), "missing canonical token dictionary"


@pytest.mark.parametrize(("schema_name", "example_name"), SCHEMA_EXAMPLE_PAIRS)
def test_anp_examples_validate_against_schemas(
    schema_name: str, example_name: str, schema_registry: Registry
) -> None:
    schema = _read_json(ANP_SCHEMA_DIR / schema_name)
    example = _read_json(ANP_EXAMPLE_DIR / example_name)

    validator = Draft202012Validator(schema=schema, registry=schema_registry)
    validator.validate(example)


def test_axp_foundation_bundle_shape() -> None:
    schema = _read_json(AXP_SCHEMA_PATH)
    dictionary = _read_json(AXP_DICTIONARY_PATH)

    assert schema["properties"]["kind"]["const"] == "AXP.AgentFoundation"
    assert "core_invariants" in schema["properties"]
    assert dictionary.get("kind") == "AXP.CanonicalTokenDictionary"
    assert isinstance(dictionary.get("families"), dict)
    assert dictionary["families"], "canonical token dictionary must contain token families"
