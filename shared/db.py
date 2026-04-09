"""shared/db module."""

import os
from contextlib import contextmanager
from threading import Lock
from typing import Any, Iterator

try:
    import psycopg  # type: ignore
except Exception:  # pragma: no cover
    psycopg = None

try:
    from psycopg_pool import ConnectionPool  # type: ignore
except Exception:  # pragma: no cover
    ConnectionPool = None

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://mea:mea@localhost:5432/mea")
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "10"))
DB_POOL_ENABLED = os.environ.get("DB_POOL_ENABLED", "true").strip().lower() in {"1", "true", "yes"}
DB_POOL_MIN_SIZE = int(os.environ.get("DB_POOL_MIN_SIZE", "1"))
DB_POOL_MAX_SIZE = int(os.environ.get("DB_POOL_MAX_SIZE", "10"))
DB_POOL_TIMEOUT_SECONDS = int(os.environ.get("DB_POOL_TIMEOUT_SECONDS", "30"))
DB_POOL_MAX_WAITING = int(os.environ.get("DB_POOL_MAX_WAITING", "20"))

_pool_lock = Lock()
_pool: Any = None


def get_pool():
    global _pool
    if not DB_POOL_ENABLED or ConnectionPool is None:
        return None
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(
                conninfo=DATABASE_URL,
                min_size=max(1, DB_POOL_MIN_SIZE),
                max_size=max(DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE),
                timeout=max(1, DB_POOL_TIMEOUT_SECONDS),
                max_waiting=max(0, DB_POOL_MAX_WAITING),
                open=True,
                kwargs={"connect_timeout": DB_CONNECT_TIMEOUT_SECONDS},
            )
    return _pool


def close_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None


def pool_health() -> dict[str, Any]:
    if not DB_POOL_ENABLED:
        return {"enabled": False, "reason": "db_pool_disabled"}
    if ConnectionPool is None:
        return {"enabled": False, "reason": "psycopg_pool_not_installed"}
    pool = get_pool()
    if pool is None:
        return {"enabled": False, "reason": "pool_unavailable"}
    try:
        stats = pool.get_stats()
    except Exception as exc:  # pragma: no cover - defensive only
        return {"enabled": True, "healthy": False, "error": str(exc)}
    return {
        "enabled": True,
        "healthy": True,
        "min_size": max(1, DB_POOL_MIN_SIZE),
        "max_size": max(DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE),
        "stats": stats,
    }


@contextmanager
def get_conn() -> Iterator[Any]:
    if psycopg is None:
        raise RuntimeError("psycopg_not_installed")
    pool = get_pool()
    if pool is not None:
        with pool.connection() as conn:
            with conn:
                yield conn
        return

    with psycopg.connect(DATABASE_URL, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
        with conn:
            yield conn
