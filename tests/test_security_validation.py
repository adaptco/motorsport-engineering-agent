import pytest
from pydantic import ValidationError
from shared.models import FixCIRequest

def test_fix_ci_request_validation_success():
    # Should pass
    FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="123")
    FixCIRequest(repo="acme.org/repo-name_123", branch="feature/branch-1", patch="diff...", run_id="run_42")

def test_fix_ci_request_validation_repo_format():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme-repo", branch="main", patch="diff...")
    assert "Repo must be in 'owner/repo' format" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo/extra", branch="main", patch="diff...")
    assert "Repo must be in 'owner/repo' format" in str(excinfo.value)

def test_fix_ci_request_validation_hyphen_prefix():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="-oProxyCommand=touch/tmp/pwn", branch="main", patch="diff...")
    assert "Repo must not start with a hyphen" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="-b", patch="diff...")
    assert "Branch must not start with a hyphen" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="-r")
    assert "Run ID must not start with a hyphen" in str(excinfo.value)

def test_fix_ci_request_validation_invalid_chars():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo; rm -rf /", branch="main", patch="diff...")
    # It fails on format check first if it contains semicolon outside of owner/repo parts
    assert "Repo must be in 'owner/repo' format" in str(excinfo.value) or "Invalid repo format" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main&&ls", patch="diff...")
    assert "Invalid branch characters" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme/repo", branch="main", patch="diff...", run_id="id$(whoami)")
    assert "Invalid run_id characters" in str(excinfo.value)

def test_fix_ci_request_validation_spaces():
    with pytest.raises(ValidationError) as excinfo:
        FixCIRequest(repo="acme repo", branch="main", patch="diff...")
    assert "Repo must be in 'owner/repo' format" in str(excinfo.value)
