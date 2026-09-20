"""Apply db/migrations/*.sql in order, once each.

Usage:  uv run python db/migrate.py            (uses DATABASE_URL, the admin role)
        uv run python db/migrate.py --status
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def applied(conn: psycopg.Connection) -> set[str]:
    conn.execute(
        "create table if not exists schema_migrations ("
        " name text primary key, applied_at timestamptz not null default now())"
    )
    return {r[0] for r in conn.execute("select name from schema_migrations")}


def main(argv: list[str]) -> int:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    with psycopg.connect(url) as conn:
        done = applied(conn)
        conn.commit()

        if "--status" in argv:
            for f in files:
                print(("applied  " if f.name in done else "pending  ") + f.name)
            return 0

        for f in files:
            if f.name in done:
                continue
            print(f"applying {f.name} ...", end=" ", flush=True)
            with conn.transaction():
                conn.execute(f.read_text())
                conn.execute("insert into schema_migrations (name) values (%s)", (f.name,))
            print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
