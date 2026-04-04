import os
from contextlib import contextmanager

try:
    import psycopg  # type: ignore
except Exception:  # pragma: no cover
    psycopg = None

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://mea:mea@localhost:5432/mea")


@contextmanager
def get_conn():
    if psycopg is None:
        raise RuntimeError("psycopg_not_installed")
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
