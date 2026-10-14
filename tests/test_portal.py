"""Admin portal smoke tests: auth gate, upload validation, book and user lifecycle."""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ["ADMIN_PASSWORD"] = "pw-test"
from api.main import app  # noqa: E402


@pytest.fixture
def client(isolate_sources, admin):
    admin.execute("delete from login_failures where key = 'admin-portal'")
    with TestClient(app) as c:
        yield c
    admin.execute("delete from login_failures where key = 'admin-portal'")


def login(c):
    r = c.post("/admin/login", data={"password": "pw-test"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/admin/books"


def test_session_secret_is_required_behind_https(monkeypatch):
    from api.main import session_secret
    monkeypatch.setenv("PUBLIC_URL", "https://guide.example.org")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        session_secret()
    monkeypatch.setenv("PUBLIC_URL", "http://localhost:8010")
    assert session_secret() == "dev-only"


def test_pages_require_login(client):
    for path in ("/admin/books", "/admin/users", "/admin/activity"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/admin/login"
    assert client.post("/admin/login", data={"password": "nope"}, follow_redirects=True).text.count("Wrong password") == 1


def test_admin_login_locks_after_repeated_failures(client):
    for _ in range(10):
        client.post("/admin/login", data={"password": "nope"})
    r = client.post("/admin/login", data={"password": "pw-test"}, follow_redirects=True)
    assert "Too many wrong attempts" in r.text and "/admin/login" in str(r.url)


def test_admin_login_refuses_empty_password_when_unset(client, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    for pw in ("", " "):   # FastAPI rejects "" itself (422); anything else must still not match an unset password
        r = client.post("/admin/login", data={"password": pw}, follow_redirects=False)
        assert r.headers.get("location") != "/admin/books"
    assert client.get("/admin/books", follow_redirects=False).headers["location"] == "/admin/login"


def test_upload_rejects_other_file_types(client):
    login(client)
    r = client.post("/admin/books", files={"file": ("notes.txt", b"hi")}, follow_redirects=True)
    assert "Only EPUB and PDF" in r.text


def test_book_upload_visibility_and_delete(client, admin, tmp_path):
    login(client)
    r = client.post("/admin/books", files={"file": ("mybook.epub", b"not really an epub")},
                    data={"title": "Portal Test Book", "author": "Dag Heward-Mills"}, follow_redirects=True)
    assert "Portal Test Book" in r.text and "pending" in r.text
    sid, vis = admin.execute("select id, visibility from sources where title = 'Portal Test Book'").fetchone()
    assert vis == "member"
    client.post(f"/admin/books/{sid}/visibility", data={"visibility": "leader"})
    assert admin.execute("select visibility from sources where id = %s", (sid,)).fetchone()[0] == "leader"
    r = client.post(f"/admin/books/{sid}/delete", follow_redirects=True)
    assert "Deleted Portal Test Book" in r.text
    assert admin.execute("select count(*) from sources where id = %s", (sid,)).fetchone()[0] == 0


def test_user_lifecycle(client, admin):
    login(client)
    email = f"portal-{uuid.uuid4().hex[:6]}@x.org"
    r = client.post("/admin/users", data={"email": email, "name": "Ama", "role": "member"}, follow_redirects=True)
    assert email in r.text
    assert "already exists" in client.post("/admin/users", data={"email": email, "role": "member"}, follow_redirects=True).text
    uid = admin.execute("select id from users where email = %s", (email,)).fetchone()[0]
    client.post(f"/admin/users/{uid}/role", data={"role": "leader"})
    assert admin.execute("select role from users where id = %s", (uid,)).fetchone()[0] == "leader"
    client.post(f"/admin/users/{uid}/delete")
    assert admin.execute("select count(*) from users where id = %s", (uid,)).fetchone()[0] == 0


def test_activity_renders_and_hides_sensitive_text(client, admin):
    login(client)
    admin.execute("insert into query_logs (question, classification, category, answer) values "
                  "('plain question about prayer', 'answerable', null, 'an answer'), "
                  "('my secret crisis text', 'answerable', 'self_harm', 'secret answer text')")
    try:
        page = client.get("/admin/activity")
        assert page.status_code == 200 and "plain question about prayer" in page.text
        assert "secret" not in page.text and "self_harm: text hidden" in page.text
    finally:
        admin.execute("delete from query_logs where question in ('plain question about prayer', 'my secret crisis text')")
