"""Unified database connection module with connection pooling.

Provides get_conn(), get_db() (alias), release_conn(), query_db(),
and db_connection() context manager. Reads DATABASE_URL from
environment variable with fallback to default.
"""

import logging
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:mes1234@postgres:5432/mes_db",
)

_pool = None


def _get_pool():
    """Lazy-initialize the threaded connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DATABASE_URL,
            connect_timeout=5,
        )
    return _pool


def get_conn():
    """Get a connection from the pool."""
    try:
        return _get_pool().getconn()
    except Exception as e:
        log.error("DB Connection Error: %s", e)
        return None


def release_conn(conn):
    """Return a connection to the pool."""
    try:
        if conn and _pool and not _pool.closed:
            _pool.putconn(conn)
    except Exception:
        pass


# Backward-compatible alias
get_db = get_conn


@contextmanager
def db_connection():
    """Context manager that auto-releases connection to pool."""
    conn = get_conn()
    try:
        yield conn
    finally:
        release_conn(conn)


def query_db(sql, params=None, fetch=True):
    """Execute SQL and return results as list of dicts.

    Args:
        sql: SQL query string.
        params: Query parameters tuple.
        fetch: If True, return fetchall(); if False, commit and return True.

    Returns:
        List of RealDictRow on fetch, True on commit, or [] on error.
    """
    conn = get_conn()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return True
    except Exception as e:
        log.error("SQL Error: %s", e)
        if not fetch:
            conn.rollback()
        return []
    finally:
        release_conn(conn)
