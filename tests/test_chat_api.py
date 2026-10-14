"""Chat API: auth, conversation ownership, streaming ask, passage visibility. No network (fake LLM)."""
import json
import os
import re
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ["SHEPHERD_EMBEDDER"] = "fake"
os.environ["SHEPHERD_RERANKER"] = "fake"

from api.chat import check_password, hash_password  # noqa: E402
from api.main import app  # noqa: E402
from shepherd import answer  # noqa: E402
from tests.test_answer import ANSWERABLE, P, fake_llm  # noqa: E402,F401


def email():
    return f"u{uuid.uuid4().hex[:8]}@example.org"


@pytest.fixture
def client(isolate_sources, admin, monkeypatch):
    made, outbox = [], []
    monkeypatch.setattr("shepherd.mail.send", lambda to, subject, body, html=None: outbox.append((to, subject, body)))
    with TestClient(app) as c:
        c.made, c.outbox = made, outbox
        yield c
    for e in made:
        admin.execute("delete from login_failures where key = lower(%s)", (e,))
        admin.execute("delete from query_logs where user_id in (select id from users where email = %s)", (e,))
        admin.execute("delete from conversations where user_id in (select id from users where email = %s)", (e,))
        admin.execute("delete from users where email = %s", (e,))


def code_for(c, e):
    return re.search(r"\b(\d{6})\b", [m for m in c.outbox if m[0] == e][-1][2]).group(1)


def signup(c, e=None, pw="correct horse", verify=True):
    e = e or email()
    c.made.append(e)
    r = c.post("/api/signup", json={"email": e, "password": pw})
    assert r.status_code == 200, r.text
    if verify:
        assert c.post("/api/verify-email", json={"code": code_for(c, e)}).status_code == 200
    return e


def sse(r):
    return [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]


def test_password_hash_roundtrip():
    h = hash_password("secret123")
    assert check_password("secret123", h) and not check_password("wrong", h) and not check_password("x", None)


def test_signup_login_logout_me(client):
    assert client.get("/api/me").status_code == 401
    e = signup(client)
    me = client.get("/api/me").json()
    assert me["email"] == e and me["role"] == "member"
    assert client.post("/api/signup", json={"email": e, "password": "another one"}).status_code == 409
    client.post("/api/logout")
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/login", json={"email": e, "password": "wrong pass"}).status_code == 401
    assert client.post("/api/login", json={"email": e.upper(), "password": "correct horse"}).status_code == 200


def test_signup_validation(client):
    assert client.post("/api/signup", json={"email": "nope", "password": "longenough"}).status_code == 422
    assert client.post("/api/signup", json={"email": email(), "password": "short"}).status_code == 422


def test_ask_streams_and_persists(client, fake_llm, monkeypatch):
    signup(client)
    monkeypatch.setattr(answer, "retrieve", lambda *a, **k: [P("grace", scripture=[43003016])])
    fake_llm(ANSWERABLE, ["Grace ", "abounds [1]."])
    evs = sse(client.post("/api/ask", json={"question": "what about grace?"}))
    assert evs[0]["type"] == "conversation" and "classification" in {e["type"] for e in evs}
    assert [e["text"] for e in evs if e["type"] == "status"] == ["Searching the books", "Writing your answer"]
    cit = next(e for e in evs if e["type"] == "citations")["citations"][0]
    assert cit["scriptures"] == ["John 3:16"] and not any(k.startswith("_") for k in cit)
    conv = evs[0]["id"]
    assert client.get("/api/conversations").json()[0]["id"] == conv
    msgs = client.get(f"/api/conversations/{conv}").json()
    assert [m["role"] for m in msgs] == ["user", "assistant"] and msgs[1]["citations"][0]["n"] == 1


def test_daily_question_cap(client, fake_llm, monkeypatch):
    import api.chat as chat
    signup(client)
    monkeypatch.setattr(chat, "DAILY_QUESTIONS", 1)
    monkeypatch.setattr(answer, "retrieve", lambda *a, **k: [P("x")])
    fake_llm(ANSWERABLE, ["ok [1]."])
    assert client.post("/api/ask", json={"question": "one"}).status_code == 200
    r = client.post("/api/ask", json={"question": "two"})
    assert r.status_code == 429 and "limit" in r.json()["detail"]


def test_conversations_are_private(client, fake_llm, monkeypatch):
    signup(client)
    monkeypatch.setattr(answer, "retrieve", lambda *a, **k: [P("x")])
    fake_llm(ANSWERABLE, ["ok [1]."])
    conv = sse(client.post("/api/ask", json={"question": "mine"}))[0]["id"]
    client.post("/api/logout")
    signup(client)                                    # a different user
    assert client.get(f"/api/conversations/{conv}").status_code == 404
    assert client.post("/api/ask", json={"question": "hijack", "conversation_id": conv}).status_code == 404
    assert client.delete(f"/api/conversations/{conv}").status_code == 404
    assert client.get("/api/conversations").json() == []


def test_deleting_a_conversation_deletes_its_logs(client, admin, fake_llm, monkeypatch):
    signup(client)
    monkeypatch.setattr(answer, "retrieve", lambda *a, **k: [P("x")])
    fake_llm(ANSWERABLE, ["ok [1]."])
    conv = sse(client.post("/api/ask", json={"question": "mine"}))[0]["id"]
    logs = lambda: admin.execute("select count(*) from query_logs where conversation_id = %s", (conv,)).fetchone()[0]  # noqa: E731
    assert logs() == 1
    assert client.delete(f"/api/conversations/{conv}").status_code == 200
    assert logs() == 0


def test_passage_respects_visibility_and_links_neighbours(client, admin):
    signup(client)
    def src(vis):
        return admin.execute("insert into sources (title, author, file_uri, visibility, status) values ('B', 'A', 's3://x/y', %s, 'ready') returning id", (vis,)).fetchone()[0]
    def chunk(sid, n, scripture=()):
        return str(admin.execute("insert into chunks (source_id, content, raw_content, location, scripture) values (%s, 't', %s, %s, %s) returning id",
                                 (sid, f"text {n}", json.dumps({"chapter": 1, "chunk": n}), list(scripture))).fetchone()[0])
    s = src("member")
    a, b, c = chunk(s, 0), chunk(s, 1, [45008028, 45008029]), chunk(s, 2)
    hidden = chunk(src("leader"), 0)
    r = client.get(f"/api/passages/{b}").json()
    assert (r["prev_id"], r["next_id"], r["text"]) == (a, c, "text 1")
    assert r["scriptures"][0]["ref"] == "Romans 8:28-29" and "good" in r["scriptures"][0]["text"]
    assert client.get(f"/api/passages/{hidden}").status_code == 404      # member cannot read leader-only
    assert client.get("/api/passages/not-a-uuid").status_code == 404


# --- profile ------------------------------------------------------------------

GOOD = {"first_name": " Ama ", "last_name": "Owusu", "date_of_birth": "1990-05-17", "ministry_role": "shepherd"}


def test_profile_starts_incomplete_then_saves(client, admin):
    signup(client)
    assert client.get("/api/me").json()["profile_complete"] is False
    assert client.put("/api/profile", json=GOOD).status_code == 200
    me = client.get("/api/me").json()
    assert me["profile_complete"] and (me["first_name"], me["name"], me["ministry_role"]) == ("Ama", "Ama Owusu", "shepherd")
    assert me["role"] == "member"                      # saying "shepherd" does not grant leader access


@pytest.mark.parametrize("bad", [
    {"ministry_role": "bishop"}, {"date_of_birth": "2999-01-01"}, {"date_of_birth": "1850-01-01"},
    {"date_of_birth": "2024-01-01"}, {"first_name": "   "},
])
def test_profile_validation(client, bad):
    signup(client)
    assert client.put("/api/profile", json={**GOOD, **bad}).status_code == 422


def test_profile_requires_sign_in(client):
    assert client.put("/api/profile", json=GOOD).status_code == 401


def test_ministry_role_reaches_the_prompt(app, admin):
    from shepherd.answer import _user
    uid = admin.execute("insert into users (email, role, name, ministry_role) values (%s, 'member', 'Kofi Boateng', 'pastor') returning id", (email(),)).fetchone()[0]
    try:
        with app.transaction():
            assert _user(app, uid) == ("Kofi Boateng, a pastor", "member")
    finally:
        admin.execute("delete from users where id = %s", (uid,))


# --- Google sign-in -------------------------------------------------------------

@pytest.fixture
def google(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("PUBLIC_URL", "http://app.test")
    info = {}
    monkeypatch.setattr("api.chat.google_userinfo", lambda code: info)
    return info


def start_google(c):
    r = c.get("/api/auth/google", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"].startswith("https://accounts.google.com/")
    from urllib.parse import parse_qs, urlparse
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["redirect_uri"] == ["http://app.test/api/auth/google/callback"]
    return q["state"][0]


def test_google_disabled_without_credentials(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    assert client.get("/api/auth/config").json() == {"google": False}
    r = client.get("/api/auth/google", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/?auth_error=google_off"


def test_google_new_user_gets_names_and_still_needs_profile(client, google):
    e = email(); client.made.append(e)
    google.update(sub=f"g-{uuid.uuid4()}", email=e.upper(), email_verified=True, given_name="Yaw", family_name="Asante")
    assert client.get("/api/auth/config").json() == {"google": True}
    state = start_google(client)
    r = client.get(f"/api/auth/google/callback?code=abc&state={state}", follow_redirects=False)
    assert r.headers["location"] == "http://app.test/"
    me = client.get("/api/me").json()
    assert (me["email"], me["first_name"], me["last_name"], me["google"], me["email_verified"]) == (e, "Yaw", "Asante", True, False)
    assert me["profile_complete"] is False
    # new Google accounts go through the code screen too
    assert client.get("/api/conversations").status_code == 403
    assert client.post("/api/verify-email", json={"code": code_for(client, e)}).status_code == 200
    assert client.get("/api/me").json()["email_verified"] is True
    assert client.post("/api/login", json={"email": e, "password": "whatever1"}).json()["detail"].startswith("This account uses Google")


def test_google_links_existing_password_account(client, google):
    e = signup(client); client.post("/api/logout")
    google.update(sub=f"g-{uuid.uuid4()}", email=e, email_verified=True, given_name="Ama", family_name="Owusu")
    client.get(f"/api/auth/google/callback?code=abc&state={start_google(client)}", follow_redirects=False)
    me = client.get("/api/me").json()
    assert me["email"] == e and me["google"] and me["first_name"] == "Ama" and me["email_verified"]   # already verified: no second code
    assert len([m for m in client.outbox if m[0] == e]) == 1
    client.post("/api/logout")
    assert client.post("/api/login", json={"email": e, "password": "correct horse"}).status_code == 200   # password still works


def test_google_rejects_bad_state_and_unverified_email(client, google):
    start_google(client)
    r = client.get("/api/auth/google/callback?code=abc&state=forged", follow_redirects=False)
    assert "auth_error=google" in r.headers["location"] and client.get("/api/me").status_code == 401
    google.update(sub="g-x", email=email(), email_verified=False)
    r = client.get(f"/api/auth/google/callback?code=abc&state={start_google(client)}", follow_redirects=False)
    assert "google_unverified" in r.headers["location"] and client.get("/api/me").status_code == 401


# --- email verification -----------------------------------------------------------

def test_signup_sends_code_and_blocks_until_verified(client):
    e = signup(client, verify=False)
    assert len(client.outbox) == 1 and client.outbox[0][0] == e and "code" in client.outbox[0][1].lower()
    assert client.get("/api/me").json()["email_verified"] is False
    for method, path in [("get", "/api/conversations"), ("put", "/api/profile"), ("post", "/api/ask")]:
        body = GOOD if path == "/api/profile" else {"question": "x"}
        assert getattr(client, method)(path, **({} if method == "get" else {"json": body})).status_code == 403
    assert client.post("/api/verify-email", json={"code": code_for(client, e)}).status_code == 200
    assert client.get("/api/me").json()["email_verified"] is True
    assert client.get("/api/conversations").status_code == 200


def test_wrong_codes_lock_after_five(client):
    e = signup(client, verify=False)
    good = code_for(client, e)
    bad = "000000" if good != "000000" else "111111"
    msgs = [client.post("/api/verify-email", json={"code": bad}).json()["detail"] for _ in range(5)]
    assert msgs[0].endswith("4 attempts left.") and msgs[3].endswith("1 attempt left.") and "Too many" in msgs[4]
    assert "Too many" in client.post("/api/verify-email", json={"code": good}).json()["detail"]   # locked even with the right code


def test_code_format_is_validated(client):
    signup(client, verify=False)
    for bad in ("12345", "abcdef", "1234567"):
        assert client.post("/api/verify-email", json={"code": bad}).status_code == 422


def test_expired_code_rejected(client, admin):
    e = signup(client, verify=False)
    admin.execute("update email_otps set expires_at = now() - interval '1 minute' where user_id = (select id from users where email = %s)", (e,))
    assert "expired" in client.post("/api/verify-email", json={"code": code_for(client, e)}).json()["detail"]


def test_resend_has_cooldown_and_replaces_code(client, admin):
    e = signup(client, verify=False)
    old = code_for(client, e)
    assert client.post("/api/resend-code").status_code == 429
    admin.execute("update email_otps set last_sent_at = now() - interval '2 minutes' where user_id = (select id from users where email = %s)", (e,))
    assert client.post("/api/resend-code").status_code == 200 and len(client.outbox) == 2
    new = code_for(client, e)
    if new != old:
        assert client.post("/api/verify-email", json={"code": old}).status_code == 400
    assert client.post("/api/verify-email", json={"code": new}).status_code == 200


def test_login_of_unverified_account_sends_fresh_code_when_none_live(client, admin):
    e = signup(client, verify=False)
    client.post("/api/logout")
    client.post("/api/login", json={"email": e, "password": "correct horse"})
    assert len(client.outbox) == 1                       # code still live: no spam
    admin.execute("update email_otps set expires_at = now() - interval '1 minute' where user_id = (select id from users where email = %s)", (e,))
    client.post("/api/logout")
    client.post("/api/login", json={"email": e, "password": "correct horse"})
    assert len(client.outbox) == 2
    assert client.post("/api/verify-email", json={"code": code_for(client, e)}).status_code == 200


def test_welcome_email_sent_once_on_first_profile_completion(client):
    e = signup(client)
    client.put("/api/profile", json=GOOD)
    welcomes = [m for m in client.outbox if m[0] == e and m[1].startswith("Welcome")]
    assert len(welcomes) == 1 and "Welcome to First Love Church, Ama" in welcomes[0][1] and "As a shepherd" in welcomes[0][2]
    client.put("/api/profile", json={**GOOD, "ministry_role": "pastor"})     # editing later: no second welcome
    assert len([m for m in client.outbox if m[1].startswith("Welcome")]) == 1


def test_failed_welcome_email_does_not_block_profile(client, monkeypatch):
    signup(client)
    def boom(*a, **k):
        raise RuntimeError("resend down")
    monkeypatch.setattr("shepherd.mail.send", boom)
    assert client.put("/api/profile", json=GOOD).status_code == 200
    assert client.get("/api/me").json()["profile_complete"] is True


def test_signup_email_failure_is_clear_and_leaves_no_account(client, admin, monkeypatch):
    import httpx
    def refused(*a, **k):
        raise httpx.HTTPStatusError("403", request=httpx.Request("POST", "https://api.resend.com/emails"), response=httpx.Response(403))
    monkeypatch.setattr("shepherd.mail.send", refused)
    e = email()
    r = client.post("/api/signup", json={"email": e, "password": "correct horse"})
    assert r.status_code == 502 and "could not send your email code" in r.json()["detail"]
    assert admin.execute("select count(*) from users where email = %s", (e,)).fetchone()[0] == 0
    assert client.get("/api/me").status_code == 401


def test_login_locks_after_ten_wrong_passwords_and_success_clears(client, admin):
    e = signup(client)
    client.post("/api/logout")
    for _ in range(9):
        assert client.post("/api/login", json={"email": e, "password": "wrong pass"}).status_code == 401
    assert client.post("/api/login", json={"email": e, "password": "correct horse"}).status_code == 200   # clears
    for _ in range(10):
        client.post("/api/login", json={"email": e, "password": "wrong pass"})
    r = client.post("/api/login", json={"email": e, "password": "correct horse"})
    assert r.status_code == 429 and "Too many wrong attempts" in r.json()["detail"]


def test_unknown_email_is_throttled_the_same_way(client, admin):
    e = email()
    client.made.append(e)          # cleanup of its failure rows
    for _ in range(10):
        assert client.post("/api/login", json={"email": e, "password": "whatever1"}).status_code == 401
    assert client.post("/api/login", json={"email": e, "password": "whatever1"}).status_code == 429


def test_book_file_streams_epub_with_visibility_and_download_name(client, admin, tmp_path):
    from shepherd import storage
    from tests.test_ingest import make_epub

    signup(client)
    sid = uuid.uuid4()
    storage.ensure_bucket()
    uri = storage.upload_book(str(sid), make_epub(tmp_path / "b.epub"))
    admin.execute("insert into sources (id, title, file_uri, visibility, status) values (%s, 'Why Loyalty?', %s, 'member', 'ready')", (sid, uri))
    hidden = admin.execute("insert into sources (title, file_uri, visibility, status) values ('L', %s, 'leader', 'ready') returning id", (uri,)).fetchone()[0]
    r = client.get(f"/api/books/{sid}/file")
    assert r.status_code == 200 and r.headers["content-type"] == "application/epub+zip" and r.content[:2] == b"PK"
    assert "content-disposition" not in r.headers
    r = client.get(f"/api/books/{sid}/file?download=1")
    assert r.headers["content-disposition"] == "attachment; filename*=UTF-8''Why%20Loyalty%3F.epub"
    assert client.get(f"/api/books/{hidden}/file").status_code == 404
    assert client.get("/api/books/nope/file").status_code == 404


def test_keep_warm_thread_runs_while_the_app_is_up(client):
    import threading
    # startup loads the models and then keeps touching them every KEEP_WARM_SECONDS (fakes here),
    # so a quiet server never evicts them: query_logs showed 8s warm vs 60s cold (2026-10-13)
    assert any(t.name == "keep-warm" and t.daemon for t in threading.enumerate())
