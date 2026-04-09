"""tests/test_webhooks module."""

import hashlib
import hmac

from fastapi.testclient import TestClient

from control_plane.app import app, validate_webhook_startup_config

client = TestClient(app)


def _signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_missing_secret_is_blocked(monkeypatch):
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr("control_plane.webhooks.store_webhook", lambda *args, **kwargs: None)

    response = client.post(
        "/github/webhook",
        headers={"x-hub-signature-256": "sha256=whatever"},
        json={"repository": {"full_name": "acme/repo"}},
    )

    assert response.status_code == 503
    assert "GITHUB_WEBHOOK_SECRET" in response.text


def test_webhook_invalid_signature_is_rejected(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setattr("control_plane.webhooks.store_webhook", lambda *args, **kwargs: None)

    response = client.post(
        "/github/webhook",
        headers={"x-hub-signature-256": "sha256=invalid"},
        json={"repository": {"full_name": "acme/repo"}},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid signature"


def test_webhook_valid_signature_is_accepted(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")

    calls: list[tuple[str, str, str | None, dict]] = []

    def _store(delivery_id, event_name, repo_slug, payload):
        calls.append((delivery_id, event_name, repo_slug, payload))

    monkeypatch.setattr("control_plane.webhooks.store_webhook", _store)
    monkeypatch.setattr("control_plane.webhooks.correlate_workflow_run", lambda *args, **kwargs: None)

    # payload = {"repository": {"full_name": "acme/repo"}}
    body = b'{"repository":{"full_name":"acme/repo"}}'

    response = client.post(
        "/github/webhook",
        headers={
            "x-github-event": "push",
            "x-github-delivery": "delivery-1",
            "x-hub-signature-256": _signature("test-secret", body),
        },
        content=body,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True}
    assert len(calls) == 1
    assert calls[0][0] == "delivery-1"
    assert calls[0][1] == "push"
    assert calls[0][2] == "acme/repo"


def test_startup_validation_fails_when_webhook_required_without_secret():
    try:
        validate_webhook_startup_config(webhook_secret=None, webhook_required=True)
        raise AssertionError("startup validation should fail without webhook secret")
    except RuntimeError as exc:
        assert "GITHUB_WEBHOOK_SECRET must be set" in str(exc)


def test_startup_validation_returns_configured_state():
    assert validate_webhook_startup_config(webhook_secret="test-secret", webhook_required=False) is True
    assert validate_webhook_startup_config(webhook_secret=None, webhook_required=False) is False
