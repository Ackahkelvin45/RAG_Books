"""Database access helpers.

The app connects as the restricted `shepherd_app` role. Transactions are plain
psycopg transactions; there is no tenant scoping (single church deployment).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from . import config


def connect(url: str | None = None) -> psycopg.Connection:
    """Open a connection as the restricted application role."""
    url = url or config.APP_DATABASE_URL
    if not url:
        raise RuntimeError("APP_DATABASE_URL is not set")
    return psycopg.connect(url)


@contextmanager
def transaction(conn: psycopg.Connection) -> Iterator[psycopg.Connection]:
    """Run a block in one transaction. Commits on success, rolls back on error."""
    with conn.transaction():
        yield conn


def lookup_user_by_email(conn: psycopg.Connection, email: str) -> dict | None:
    """Pre-auth lookup: email -> user/role, via the security-definer function."""
    row = conn.execute(
        "select user_id, role from auth_lookup_user(%s)", (email,)
    ).fetchone()
    if row is None:
        return None
    return {"user_id": row[0], "role": row[1]}
