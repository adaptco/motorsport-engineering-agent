"""tests/test_model_weights module."""

from pathlib import Path

import yaml


def test_model_weights_sum_reasonably():
    weights = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "config" / "model_weights.yaml").read_text()
    )
    total = sum(weights["supervisor_reward_weights"].values())
    assert 0.99 <= total <= 1.01
