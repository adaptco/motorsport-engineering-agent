"""tests/test_security_validation module."""

import pytest
from pydantic import ValidationError
from shared.models import FixCIRequest

def test_fix_ci_request_validation_success():
    # Should pass
    FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="123")
    FixCIRequest(repo="acme-repo_123", branch="feature/branch-1", patch="diff...", run_id="run_42")

def test_fix_ci_request_validation_hyphen_prefix():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="-oProxyCommand=touch/tmp/pwn", branch="main", patch="diff...")
    assert "String must not start with a hyphen" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="-b", patch="diff...")
    assert "String must not start with a hyphen" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="-r")
    assert "String must not start with a hyphen" in str(excinfo.value)

def test_fix_ci_request_validation_invalid_chars():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo; rm -rf /", branch="main", patch="diff...")
    assert "String contains invalid characters" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main&&ls", patch="diff...")
    assert "String contains invalid characters" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="id$(whoami)")
    assert "String contains invalid characters" in str(excinfo.value)

def test_fix_ci_request_validation_spaces():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme repo", branch="main", patch="diff...")
    assert "String contains invalid characters" in str(excinfo.value)
