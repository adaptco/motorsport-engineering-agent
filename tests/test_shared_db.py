from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shared import db


def test_pool_health_disabled(monkeypatch) -> None:
    monkeypatch.setattr(db, "DB_POOL_ENABLED", False)
    health = db.pool_health()
    assert health["enabled"] is False
    assert health["reason"] == "db_pool_disabled"


def test_pool_health_no_psycopg_pool(monkeypatch) -> None:
    monkeypatch.setattr(db, "DB_POOL_ENABLED", True)
    monkeypatch.setattr(db, "ConnectionPool", None)
    health = db.pool_health()
    assert health["enabled"] is False
    assert health["reason"] == "psycopg_pool_not_installed"


def test_pool_health_healthy(monkeypatch) -> None:
    monkeypatch.setattr(db, "DB_POOL_ENABLED", True)
    mock_pool = MagicMock()
    mock_pool.get_stats.return_value = {"connections": 2}
    monkeypatch.setattr(db, "_pool", mock_pool)
    monkeypatch.setattr(db, "ConnectionPool", MagicMock())

    health = db.pool_health()
    assert health["enabled"] is True
    assert health["healthy"] is True
    assert health["stats"] == {"connections": 2}


def test_get_pool_and_close_pool(monkeypatch) -> None:
    db.close_pool()
    assert db._pool is None

    mock_pool_cls = MagicMock()
    mock_pool_instance = MagicMock()
    mock_pool_cls.return_value = mock_pool_instance

    monkeypatch.setattr(db, "DB_POOL_ENABLED", True)
    monkeypatch.setattr(db, "ConnectionPool", mock_pool_cls)

    pool = db.get_pool()
    assert pool is mock_pool_instance
    assert db.get_pool() is mock_pool_instance  # Cached return

    db.close_pool()
    assert db._pool is None
    mock_pool_instance.close.assert_called_once()


def test_get_conn_with_pool(monkeypatch) -> None:
    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn

    monkeypatch.setattr(db, "get_pool", lambda: mock_pool)
    monkeypatch.setattr(db, "psycopg", MagicMock())

    with db.get_conn() as conn:
        assert conn is mock_conn


def test_get_conn_without_pool(monkeypatch) -> None:
    mock_conn = MagicMock()
    mock_psycopg = MagicMock()
    mock_psycopg.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn

    monkeypatch.setattr(db, "get_pool", lambda: None)
    monkeypatch.setattr(db, "psycopg", mock_psycopg)

    with db.get_conn() as conn:
        assert conn is mock_conn


def test_get_conn_missing_psycopg(monkeypatch) -> None:
    monkeypatch.setattr(db, "psycopg", None)
    with pytest.raises(RuntimeError, match="psycopg_not_installed"):
        with db.get_conn():
            pass
