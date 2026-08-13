from __future__ import annotations

import pytest

from mcp_tools.mea_ci_guardrail import run_mea_ci_guardrail


def test_guardrail_missing_patch() -> None:
    res = run_mea_ci_guardrail({"ci_state": "failed", "proposed_patch": None})
    assert res["uncertain"] is True
    assert res["safe_action"] == "ask_clarifying_question"
    assert res["normalized_patch"] is None


def test_guardrail_patch_too_large() -> None:
    large_patch = "\n".join(["+++ src/file.py"] + ["+line"] * 505)
    res = run_mea_ci_guardrail({"ci_state": "failed", "proposed_patch": large_patch})
    assert res["uncertain"] is True
    assert res["safe_action"] == "do_nothing"
    assert "Patch too large" in res["reason"]


def test_guardrail_unrelated_paths() -> None:
    patch = "--- a/docs/README.md\n+++ b/docs/README.md\n+doc change\n"
    res = run_mea_ci_guardrail({"ci_state": "failed", "proposed_patch": patch})
    assert res["uncertain"] is True
    assert res["safe_action"] == "do_nothing"
    assert "not appear related" in res["reason"]


def test_guardrail_valid_ci_patch() -> None:
    patch = "--- a/src/app.py\n+++ b/src/app.py\n+import sys\n"
    res = run_mea_ci_guardrail({"ci_state": "failed", "proposed_patch": patch})
    assert res["uncertain"] is False
    assert res["safe_action"] == "emit_patch"
    assert res["normalized_patch"] == patch


def test_guardrail_valid_tests_patch() -> None:
    patch = "--- a/tests/test_app.py\n+++ b/tests/test_app.py\n+def test_something(): pass\n"
    res = run_mea_ci_guardrail({"ci_state": "failed", "proposed_patch": patch})
    assert res["uncertain"] is False
    assert res["safe_action"] == "emit_patch"
