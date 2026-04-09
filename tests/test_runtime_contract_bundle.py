import json
from pathlib import Path


def test_schema_loadable():
    """Ensure that the runtime contract bundle can be loaded as valid JSON."""
    schema_path = Path(__file__).resolve().parents[1] / "contracts/runtime/agent_runtime_contract_bundle.schema.json"
    with schema_path.open() as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "$schema" in data
    # Check that at least one event definition exists.
    assert "oneOf" in data and len(data["oneOf"]) > 0