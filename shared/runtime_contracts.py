from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@lru_cache(maxsize=1)
def _runtime_contract_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[1] / "contracts" / "runtime" / "agent_runtime_contract_bundle.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_runtime_event(event: dict[str, Any]) -> None:
    validator = _runtime_contract_validator()
    validator.validate(event)

