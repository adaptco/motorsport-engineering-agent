"""Frontend static asset and API connectivity tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from control_plane.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_index_html_served(client):
    """Root route returns the Mission Control SPA."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MEA Mission Control" in response.text
    assert '<script src="/static/app.js">' in response.text


def test_static_css_served(client):
    """Stylesheet is reachable under /static."""
    response = client.get("/static/styles.css")
    assert response.status_code == 200
    assert "--bg-primary" in response.text


def test_static_js_served(client):
    """Application script is reachable under /static."""
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "setTab" in response.text


def test_api_discovery_endpoint(client):
    """/api/routes lists available control-plane routes."""
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    paths = {r["path"] for r in data["routes"]}
    assert "/healthz" in paths
    assert "/runtime/sessions" in paths
    assert "/ingest/normalize" in paths


def test_healthz_reachable(client):
    """Health endpoint returns expected shape."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "kernel_version" in data
