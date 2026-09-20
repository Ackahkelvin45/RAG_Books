import contextlib
import io
import os
import uuid

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv()

# Tests run against their own database and bucket, never the real library.
# Set before any shepherd module is imported (config reads env at import time).
TEST_DB = "shepherd_test"
_real_admin = os.environ["DATABASE_URL"]
_to_test = lambda url: url.rsplit("/", 1)[0] + "/" + TEST_DB  # noqa: E731
os.environ["DATABASE_URL"] = _to_test(_real_admin)
os.environ["APP_DATABASE_URL"] = _to_test(os.environ["APP_DATABASE_URL"])
os.environ["S3_BUCKET"] = "shepherd-books-test"

with psycopg.connect(_real_admin, autocommit=True) as _c:
    if not _c.execute("select 1 from pg_database where datname = %s", (TEST_DB,)).fetchone():
        _c.execute(f"create database {TEST_DB}")
from db.migrate import main as _migrate  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    _migrate([])

ADMIN_URL = os.environ["DATABASE_URL"]
APP_URL = os.environ["APP_DATABASE_URL"]


@pytest.fixture
def admin(isolate_sources):
    """Superuser connection. Used only to set up and tear down fixtures."""
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        yield conn


@pytest.fixture
def app(isolate_sources):
    """Restricted application role."""
    with psycopg.connect(APP_URL) as conn:
        yield conn


@pytest.fixture
def isolate_sources():
    """Every source (and its chunks, via cascade) created during a test is removed
    afterwards, so the shared dev database keeps only real books between runs.
    Tests that rely on an empty queue also require no pending rows to exist first."""
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        before = {r[0] for r in conn.execute("select id from sources")}
        pending = conn.execute("select count(*) from sources where status in ('pending','processing')").fetchone()[0]
        if pending:
            pytest.fail(
                f"{pending} source(s) already pending/processing in the dev DB; "
                "run the worker or delete them before testing"
            )
        yield
        after = {r[0] for r in conn.execute("select id from sources")}
        new = list(after - before)
        if new:
            conn.execute("delete from sources where id = any(%s)", (new,))


@pytest.fixture
def source(admin):
    """One throwaway source with one chunk."""
    sid = admin.execute(
        "insert into sources (title, file_uri, status) "
        "values ('Book A', 's3://x/a.epub', 'ready') returning id"
    ).fetchone()[0]
    chunk = admin.execute(
        "insert into chunks (source_id, content, raw_content, location) "
        "values (%s, 'From Book A. grace abounds', 'grace abounds', '{\"chapter\": 1}') "
        "returning id",
        (sid,),
    ).fetchone()[0]
    yield {"src": sid, "chunk": chunk}
