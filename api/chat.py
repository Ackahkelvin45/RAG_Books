"""JSON API for the React chat app (web/). Mounted under /api by api/main.py.

Auth is email + password, session cookie (same SessionMiddleware as the admin portal).
New sign-ups are members; an admin promotes shepherds/pastors to leader in the portal.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import threading
import uuid
from typing import Literal
from urllib.parse import urlencode

import httpx

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from urllib.parse import quote
from pydantic import BaseModel, Field, field_validator

import logging

from shepherd import emails, mail, storage
from shepherd.answer import ask
from shepherd.db import connect, transaction
from shepherd.retrieve import visibility_clause
import pythonbible as pb

from shepherd.scripture import verse_text

router = APIRouter(prefix="/api")
log = logging.getLogger("api.chat")


# --- response shapes (documentation + output filtering) ---------------------------------------

class OK(BaseModel):
    ok: bool = True


class Me(BaseModel):
    id: str
    email: str
    name: str | None = Field(None, description="First + last name once the profile is complete.")
    role: Literal["member", "leader", "admin"] = Field(description="Access level, set by an admin. `leader`/`admin` also see leaders-only books.")
    first_name: str | None
    last_name: str | None
    date_of_birth: str | None = Field(None, examples=["1990-05-17"])
    ministry_role: Literal["member", "shepherd", "pastor"] | None = Field(None, description="What the person said they are. Shown to the AI; grants no access.")
    google: bool = Field(description="Signed in with Google at least once.")
    email_verified: bool = Field(description="False until the 6-digit email code is confirmed (every new account, email or Google).")
    profile_complete: bool = Field(description="False until names, date of birth and ministry role are saved.")


class Location(BaseModel):
    chapter: int | None = None
    title: str | None = Field(None, description="Chapter title.")
    page: int | None = None


class Citation(BaseModel):
    n: int = Field(description="The number used in the answer text, e.g. [2].")
    chunk_id: str = Field(description="Passage id; open it with GET /api/passages/{chunk_id}.")
    title: str = Field(description="Book title.")
    author: str | None
    location: Location
    raw_content: str = Field(description="The exact passage text.")
    scriptures: list[str] = Field([], examples=[["Romans 8:28", "John 3:16"]])
    url: str | None = Field(None, examples=["/read/0b3e5399-6589-4bf3-8dcc-d607de3941a4"])


class ConversationSummary(BaseModel):
    id: str
    title: str | None = Field(description="The first question, trimmed.")
    updated_at: str


class MessageOut(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation]
    created_at: str


class Verse(BaseModel):
    ref: str = Field(examples=["Romans 8:28-29"])
    text: str = Field(description="American Standard Version text (public domain).")


class PassageOut(BaseModel):
    id: str
    source_id: str = Field(description="The book; open it with GET /api/books/{source_id}/file.")
    title: str
    author: str | None
    location: Location
    text: str
    scriptures: list[Verse]
    prev_id: str | None = Field(description="Previous passage in the same book, for reading on.")
    next_id: str | None


# --- passwords (stdlib scrypt, no extra dependency) --------------------------------

def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    return salt.hex() + "$" + hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def check_password(pw: str, stored: str | None) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    got = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()
    return hmac.compare_digest(got, digest)


# --- deps ---------------------------------------------------------------------------

def db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def current_user(request: Request, conn=Depends(db)) -> dict:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "not signed in")
    with transaction(conn):
        row = conn.execute(
            "select id, email, name, role, first_name, last_name, date_of_birth, ministry_role, google_sub is not null, email_verified "
            "from users where id = %s", (uid,)).fetchone()
    if not row:
        request.session.pop("user_id", None)
        raise HTTPException(401, "not signed in")
    first, last, dob, ministry = row[4], row[5], row[6], row[7]
    return {"id": str(row[0]), "email": row[1], "name": row[2], "role": row[3],
            "first_name": first, "last_name": last, "date_of_birth": dob.isoformat() if dob else None,
            "ministry_role": ministry, "google": row[8], "email_verified": row[9],
            "profile_complete": bool(first and last and dob and ministry)}


def verified_user(user=Depends(current_user)) -> dict:
    """Everything past sign-up requires a confirmed email address."""
    if not user["email_verified"]:
        raise HTTPException(403, "Please confirm your email address first.")
    return user


# --- auth ---------------------------------------------------------------------------

class SignIn(BaseModel):
    email: str = Field(max_length=254, examples=["ama@example.org"])
    password: str = Field(max_length=200, examples=["correct horse battery"])

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Enter a valid email address.")
        return v


class SignUp(SignIn):
    password: str = Field(min_length=8, max_length=200, examples=["correct horse battery"])


@router.post("/signup", tags=["Auth"], summary="Create an account with email and password", response_model=OK, responses={409: {"description": "Email already registered"}, 502: {"description": "The code email could not be sent; no account was created"}})
def signup(body: SignUp, request: Request, conn=Depends(db)):
    """Creates a **member** account, signs the person in (session cookie) and emails a 6-digit code.
    Next step: `POST /api/verify-email`."""
    try:
        with transaction(conn):
            uid = conn.execute(
                "insert into users (email, role, password_hash) values (%s, 'member', %s) returning id",
                (body.email.lower(), hash_password(body.password))).fetchone()[0]
            send_otp(conn, uid, body.email.lower())
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "An account with this email already exists.")
    except httpx.HTTPError:   # Resend refused or unreachable: the account is rolled back, nothing half-made
        log.exception("sign-up code email to %s failed", body.email)
        raise HTTPException(502, "We could not send your email code right now. Please try again in a few minutes.")
    request.session["user_id"] = str(uid)
    return {"ok": True}


# --- sign-in throttling (per account, not per IP: behind a proxy everyone shares one address) ------

LOGIN_MAX_FAILURES = 10
LOGIN_WINDOW_MIN = 15


def login_locked(conn, key: str) -> bool:
    return conn.execute(
        "select count(*) from login_failures where key = %s and at > now() - %s * interval '1 minute'",
        (key, LOGIN_WINDOW_MIN)).fetchone()[0] >= LOGIN_MAX_FAILURES


def record_login(conn, key: str, ok: bool) -> None:
    """A success clears the account's failures; a failure adds one."""
    if ok:
        conn.execute("delete from login_failures where key = %s", (key,))
    else:
        conn.execute("insert into login_failures (key) values (%s)", (key,))


LOCKED = f"Too many wrong attempts. Please wait {LOGIN_WINDOW_MIN} minutes and try again."


@router.post("/login", tags=["Auth"], summary="Sign in with email and password", response_model=OK, responses={401: {"description": "Wrong email or password, or a Google-only account"}, 429: {"description": f"{LOGIN_MAX_FAILURES} wrong passwords in {LOGIN_WINDOW_MIN} minutes"}})
def login(body: SignIn, request: Request, conn=Depends(db)):
    """Sets the session cookie. **In Swagger, call this first**; later \"Try it out\" calls then run as this user.
    An unverified account with no live code is sent a fresh one. After 10 wrong passwords in 15 minutes the
    account refuses sign-in (even with the right password) until the window passes."""
    key = body.email.lower()
    with transaction(conn):
        if login_locked(conn, key):   # checked for unknown emails too, so the lock reveals nothing
            raise HTTPException(429, LOCKED)
        row = conn.execute("select id, password_hash from users where lower(email) = lower(%s)", (body.email,)).fetchone()
        ok = bool(row and row[1] and check_password(body.password, row[1]))
        if not (row and not row[1]):      # a Google-only account is not a guess
            record_login(conn, key, ok)
    if row and not row[1]:
        raise HTTPException(401, "This account uses Google. Please continue with Google.")
    if not ok:
        raise HTTPException(401, "Wrong email or password.")
    with transaction(conn):
        live = conn.execute(
            "select u.email_verified, o.expires_at > now() from users u left join email_otps o on o.user_id = u.id where u.id = %s",
            (row[0],)).fetchone()
        if not live[0] and not live[1]:
            send_otp(conn, row[0], body.email)
    request.session["user_id"] = str(row[0])
    return {"ok": True}


@router.post("/logout", tags=["Auth"], summary="Sign out", response_model=OK)
def logout(request: Request):
    request.session.pop("user_id", None)
    return {"ok": True}


@router.get("/me", tags=["Auth"], summary="Who is signed in", response_model=Me, responses={401: {"description": "Not signed in"}})
def me(user=Depends(current_user)):
    """The app uses `email_verified` and `profile_complete` to decide which screen to show:
    sign-in → verify email → profile → chat."""
    return user


# --- email verification (6-digit code) ------------------------------------------------------

OTP_TTL_MIN = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 60


def _otp_hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def send_otp(conn, user_id, email: str) -> None:
    """Create (or replace) the user's code and email it. Caller holds a transaction."""
    code = f"{secrets.randbelow(10**6):06d}"
    conn.execute(
        "insert into email_otps (user_id, code_hash, expires_at, attempts, last_sent_at) "
        "values (%s, %s, now() + %s * interval '1 minute', 0, now()) "
        "on conflict (user_id) do update set code_hash = excluded.code_hash, expires_at = excluded.expires_at, "
        "attempts = 0, last_sent_at = now()",
        (user_id, _otp_hash(code), OTP_TTL_MIN))
    subject, text, html = emails.otp_email(code, OTP_TTL_MIN)
    mail.send(email, subject, text, html)


class Code(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$", examples=["203061"])


@router.post("/verify-email", tags=["Email verification"], summary="Confirm the 6-digit email code", response_model=OK, responses={400: {"description": "Wrong, expired or locked code (message says which)"}})
def verify_email(body: Code, user=Depends(current_user), conn=Depends(db)):
    """Codes expire after 10 minutes. Five wrong tries lock the code until a new one is requested."""
    if user["email_verified"]:
        return {"ok": True}
    with transaction(conn):
        row = conn.execute("select code_hash, expires_at < now(), attempts from email_otps where user_id = %s for update",
                           (user["id"],)).fetchone()
        if not row:
            raise HTTPException(400, "No code is active. Please request a new one.")
        code_hash, expired, attempts = row
        if expired:
            raise HTTPException(400, "This code has expired. Please request a new one.")
        if attempts >= OTP_MAX_ATTEMPTS:
            raise HTTPException(400, "Too many wrong attempts. Please request a new code.")
        wrong = not hmac.compare_digest(code_hash, _otp_hash(body.code))
        if wrong:   # count the attempt; raise only after this transaction commits, or the count rolls back
            conn.execute("update email_otps set attempts = attempts + 1 where user_id = %s", (user["id"],))
        else:
            conn.execute("update users set email_verified = true where id = %s", (user["id"],))
            conn.execute("delete from email_otps where user_id = %s", (user["id"],))
    if wrong:
        left = OTP_MAX_ATTEMPTS - attempts - 1
        raise HTTPException(400, f"That code is not right. {left} attempt{'s' if left != 1 else ''} left." if left else
                            "Too many wrong attempts. Please request a new code.")
    return {"ok": True}


@router.post("/resend-code", tags=["Email verification"], summary="Email a new code", response_model=OK, responses={429: {"description": "Asked again within 60 seconds"}})
def resend_code(user=Depends(current_user), conn=Depends(db)):
    if user["email_verified"]:
        return {"ok": True}
    with transaction(conn):
        wait = conn.execute(
            "select ceil(extract(epoch from last_sent_at + %s * interval '1 second' - now())) from email_otps where user_id = %s",
            (OTP_RESEND_SECONDS, user["id"])).fetchone()
        if wait and wait[0] and wait[0] > 0:
            raise HTTPException(429, f"Please wait {int(wait[0])} seconds before asking for another code.")
        try:
            send_otp(conn, user["id"], user["email"])
        except httpx.HTTPError:
            log.exception("resend code to %s failed", user["email"])
            raise HTTPException(502, "We could not send your email code right now. Please try again in a few minutes.")
    return {"ok": True}


# --- profile (asked once, right after sign-up) -------------------------------------------

class Profile(BaseModel):
    first_name: str = Field(min_length=1, max_length=60, examples=["Ama"])
    last_name: str = Field(min_length=1, max_length=60, examples=["Owusu"])
    date_of_birth: dt.date = Field(examples=["1990-05-17"])
    ministry_role: Literal["member", "shepherd", "pastor"] = Field(description="What the person is in church. Does not grant access.")

    @field_validator("first_name", "last_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Required.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _dob(cls, v: dt.date) -> dt.date:
        today = dt.date.today()
        if v > today or v.year < 1900:
            raise ValueError("Enter a real date of birth.")
        if (today - v).days < 365 * 5:
            raise ValueError("Enter a real date of birth.")
        return v


@router.put("/profile", tags=["Profile"], summary="Save name, date of birth and ministry role", response_model=OK, responses={403: {"description": "Email not verified yet"}})
def save_profile(body: Profile, user=Depends(verified_user), conn=Depends(db)):
    """Required once after sign-up. The first save also sends the welcome email."""
    with transaction(conn):
        conn.execute(
            "update users set first_name = %s, last_name = %s, name = %s, date_of_birth = %s, ministry_role = %s where id = %s",
            (body.first_name, body.last_name, f"{body.first_name} {body.last_name}", body.date_of_birth, body.ministry_role, user["id"]))
    if not user["profile_complete"]:      # first completion only: welcome them once
        try:
            mail.send(user["email"], *emails.welcome_email(body.first_name, body.ministry_role))
        except Exception:  # noqa: BLE001 - a failed welcome email must not block the account
            log.exception("welcome email to %s failed", user["email"])
    return {"ok": True}


# --- Google sign-in (OAuth 2.0 authorization code flow) --------------------------------------
# Needs GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET from Google Cloud Console, and PUBLIC_URL
# (where the browser reaches the app). Authorised redirect URI: {PUBLIC_URL}/api/auth/google/callback

def _google_conf():
    cid, secret = os.environ.get("GOOGLE_CLIENT_ID"), os.environ.get("GOOGLE_CLIENT_SECRET")
    base = os.environ.get("PUBLIC_URL", "http://localhost:8010").rstrip("/")
    return (cid, secret, base) if cid and secret else None


@router.get("/auth/config", tags=["Google sign-in"], summary="Is Google sign-in switched on")
def auth_config():
    return {"google": _google_conf() is not None}


@router.get("/auth/google", tags=["Google sign-in"], summary="Start Google sign-in (browser redirect)")
def google_start(request: Request):
    """Open in a browser, not with Try it out: it redirects to Google, which returns to the callback below."""
    conf = _google_conf()
    if not conf:   # button is always shown; tell the person instead of a raw error page
        return RedirectResponse("/?auth_error=google_off")
    cid, _, base = conf
    state = secrets.token_urlsafe(24)
    request.session["google_state"] = state
    q = urlencode({"client_id": cid, "redirect_uri": f"{base}/api/auth/google/callback", "response_type": "code",
                   "scope": "openid email profile", "state": state, "prompt": "select_account"})
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{q}")


def google_userinfo(code: str) -> dict:
    """Exchange the code for tokens, then read the verified profile. Server-to-server over TLS."""
    cid, secret, base = _google_conf()
    with httpx.Client(timeout=15) as h:
        tok = h.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": cid, "client_secret": secret,
            "redirect_uri": f"{base}/api/auth/google/callback", "grant_type": "authorization_code"})
        tok.raise_for_status()
        info = h.get("https://openidconnect.googleapis.com/v1/userinfo",
                     headers={"Authorization": f"Bearer {tok.json()['access_token']}"})
        info.raise_for_status()
        return info.json()


@router.get("/auth/google/callback", tags=["Google sign-in"], summary="Google returns here (browser redirect)")
def google_callback(request: Request, code: str = "", state: str = "", error: str = "", conn=Depends(db)):
    """Creates or links the account, signs the person in, and redirects to the app. A new account is emailed
    a 6-digit code first, exactly like email sign-up."""
    conf = _google_conf()
    base = conf[2] if conf else ""
    expected = request.session.pop("google_state", None)
    if error or not code or not expected or not hmac.compare_digest(state, expected):
        return RedirectResponse(f"{base}/?auth_error=google")
    try:
        info = google_userinfo(code)
    except Exception:  # noqa: BLE001 - any failure talking to Google = sign-in failed
        return RedirectResponse(f"{base}/?auth_error=google")
    if not info.get("email") or not info.get("email_verified"):
        return RedirectResponse(f"{base}/?auth_error=google_unverified")
    email, sub = info["email"].lower(), info["sub"]
    first, last = info.get("given_name"), info.get("family_name")
    with transaction(conn):
        row = conn.execute("select id from users where google_sub = %s", (sub,)).fetchone() or \
              conn.execute("select id from users where lower(email) = %s", (email,)).fetchone()
        if row:   # existing account: link Google, fill names only if still empty
            uid, is_new = row[0], False
            conn.execute(
                "update users set google_sub = %s, first_name = coalesce(first_name, %s), last_name = coalesce(last_name, %s), "
                "name = coalesce(name, nullif(trim(concat_ws(' ', %s::text, %s::text)), '')) where id = %s",
                (sub, first, last, first, last, uid))
        else:     # new account: same journey as email sign-up (code screen, then profile)
            uid, is_new = conn.execute(
                "insert into users (email, role, google_sub, first_name, last_name, name) values (%s, 'member', %s, %s, %s, %s) returning id",
                (email, sub, first, last, " ".join(x for x in (first, last) if x) or None)).fetchone()[0], True
    if is_new:
        try:
            with transaction(conn):
                send_otp(conn, uid, email)
        except httpx.HTTPError:   # account exists; the code screen's "Resend code" can retry
            log.exception("sign-up code email to %s failed", email)
    request.session["user_id"] = str(uid)
    return RedirectResponse(f"{base}/")


# --- conversations --------------------------------------------------------------------

@router.get("/conversations", tags=["Chat"], summary="List my conversations, newest first", response_model=list[ConversationSummary])
def conversations(user=Depends(verified_user), conn=Depends(db)):
    with transaction(conn):
        rows = conn.execute(
            "select id, title, updated_at from conversations where user_id = %s order by updated_at desc limit 200",
            (user["id"],)).fetchall()
    return [{"id": str(r[0]), "title": r[1], "updated_at": r[2].isoformat()} for r in rows]


def _own(conn, conversation_id: str, user_id: str):
    try:
        uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(404, "not found")
    if not conn.execute("select 1 from conversations where id = %s and user_id = %s", (conversation_id, user_id)).fetchone():
        raise HTTPException(404, "not found")


@router.get("/conversations/{conversation_id}", tags=["Chat"], summary="All messages in one of my conversations", response_model=list[MessageOut], responses={404: {"description": "Not found or not yours"}})
def conversation(conversation_id: str, user=Depends(verified_user), conn=Depends(db)):
    with transaction(conn):
        _own(conn, conversation_id, user["id"])
        rows = conn.execute(
            "select id, role, content, citations, created_at from messages where conversation_id = %s order by created_at",
            (conversation_id,)).fetchall()
    return [{"id": str(r[0]), "role": r[1], "content": r[2], "citations": r[3], "created_at": r[4].isoformat()} for r in rows]


@router.delete("/conversations/{conversation_id}", tags=["Chat"], summary="Delete one of my conversations", response_model=OK)
def delete_conversation(conversation_id: str, user=Depends(verified_user), conn=Depends(db)):
    with transaction(conn):
        _own(conn, conversation_id, user["id"])
        conn.execute("delete from query_logs where conversation_id = %s", (conversation_id,))
        conn.execute("delete from conversations where id = %s", (conversation_id,))
    return {"ok": True}


# --- ask (server-sent events) -----------------------------------------------------------

class Ask(BaseModel):
    model_config = {"json_schema_extra": {"examples": [{"question": "How do I know if someone is becoming disloyal?"}]}}
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(None, description="Omit to start a new conversation; pass one of yours to ask a follow-up.")


class EventStream(StreamingResponse):
    media_type = "text/event-stream"   # so the docs show the stream, not JSON


# Each question is seconds of the one CPU core plus a paid model call, so: one question at a time per
# person, and a rolling daily cap. Searches themselves queue behind shepherd.retrieve.GATE.
DAILY_QUESTIONS = int(os.environ.get("SHEPHERD_DAILY_QUESTIONS", "100"))   # per user, last 24 h; 0 = no cap
BUSY = "Please wait for your current answer to finish."
_inflight: set[str] = set()
_inflight_lock = threading.Lock()


@router.post("/ask", tags=["Chat"], summary="Ask a question (answer streams back)", response_class=EventStream, responses={
    200: {"description": "Server-sent events, one JSON object per `data:` line", "content": {"text/event-stream": {"example":
        'data: {"type": "conversation", "id": "8c1f…"}\n\n'
        'data: {"type": "classification", "label": "answerable", "category": null, "language": "en", "source": "model"}\n\n'
        'data: {"type": "text", "text": "Becoming disloyal is a process"}\n\n'
        'data: {"type": "text", "text": ", not something that happens overnight [2]."}\n\n'
        'data: {"type": "citations", "citations": [{"n": 2, "chunk_id": "fe8f…", "title": "Loyalty and Disloyalty", "location": {"chapter": 2}}]}\n\n'
        'data: {"type": "text", "text": "\\n\\nBishop Dag Heward-Mills talks about this in chapter 2 of *Loyalty and Disloyalty*."}\n\n'}}},
    404: {"description": "conversation_id is not yours"},
    429: {"description": "A question of yours is still being answered, or today's limit is reached"}})
def ask_endpoint(body: Ask, user=Depends(verified_user), conn=Depends(db)):
    """Runs the full pipeline: classify → search the books → answer from the passages only.

    Events, in order: `conversation` (id to use for follow-ups), `classification`, several `text`
    pieces (join them), `citations`, then closing `text` pieces (the "talks about this in chapter X"
    line and the scriptures line). An `error` event means the answer failed part-way.
    Swagger shows the whole stream once it finishes; the app renders it live."""
    with transaction(conn):
        if body.conversation_id:
            _own(conn, body.conversation_id, user["id"])
        asked = conn.execute("select count(*) from query_logs where user_id = %s and created_at > now() - interval '1 day'",
                             (user["id"],)).fetchone()[0]
    if DAILY_QUESTIONS and asked >= DAILY_QUESTIONS:
        raise HTTPException(429, f"You have reached today's limit of {DAILY_QUESTIONS} questions. Please come back tomorrow.")
    with _inflight_lock:
        if user["id"] in _inflight:
            raise HTTPException(429, BUSY)
        _inflight.add(user["id"])

    def events():
        c = connect()          # the request's conn closes when the handler returns; the stream needs its own
        try:
            for ev in ask(c, body.question.strip(), user["id"], body.conversation_id):
                if ev["type"] == "citations":
                    ev = {**ev, "citations": [{k: v for k, v in x.items() if not k.startswith("_")} for x in ev["citations"]]}
                yield f"data: {json.dumps(ev, default=str)}\n\n"
        except Exception as e:  # noqa: BLE001 - tell the client, don't hang the stream
            yield f"data: {json.dumps({'type': 'error', 'message': 'Something went wrong. Please try again.'})}\n\n"
            raise e
        finally:
            c.close()
            with _inflight_lock:
                _inflight.discard(user["id"])

    return EventStream(events(), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# --- read a passage -------------------------------------------------------------------------

@router.get("/passages/{chunk_id}", tags=["Passages"], summary="Read one cited passage", response_model=PassageOut, responses={404: {"description": "Unknown, or a leaders-only book for a member"}})
def passage(chunk_id: str, user=Depends(verified_user), conn=Depends(db)):
    """What a citation link opens: the passage, its book and chapter, the verses it cites (ASV text), and
    previous/next passage ids for reading on."""
    try:
        uuid.UUID(chunk_id)
    except ValueError:
        raise HTTPException(404, "not found")
    with transaction(conn):
        row = conn.execute(
            "select c.id, c.source_id, c.raw_content, c.location, c.scripture, s.title, s.author "
            f"from chunks c join sources s on s.id = c.source_id where c.id = %s and {visibility_clause(user['role'])}",
            (chunk_id,)).fetchone()
        if not row:
            raise HTTPException(404, "not found")
        _, source_id, text, loc, scripture, title, author = row
        order = "coalesce((c.location->>'chapter')::int, 0), (c.location->>'chunk')::int"
        me_key = (loc.get("chapter") or 0, loc.get("chunk") or 0)
        prev = conn.execute(
            f"select c.id from chunks c where c.source_id = %s and ({order}) < (%s, %s) order by {order} desc limit 1",
            (source_id, *me_key)).fetchone()
        nxt = conn.execute(
            f"select c.id from chunks c where c.source_id = %s and ({order}) > (%s, %s) order by {order} limit 1",
            (source_id, *me_key)).fetchone()
    scriptures = []
    for ref in pb.convert_verse_ids_to_references(sorted(set(scripture or [])))[:12]:
        parts = []
        for v in pb.convert_reference_to_verse_ids(ref)[:6]:
            try:
                parts.append(verse_text(v))
            except Exception:  # noqa: BLE001 - some ids have no ASV text
                pass
        scriptures.append({"ref": pb.format_scripture_references([ref]), "text": " ".join(parts)})
    return {"id": chunk_id, "source_id": str(source_id), "title": title, "author": author, "location": loc, "text": text,
            "scriptures": scriptures, "prev_id": str(prev[0]) if prev else None, "next_id": str(nxt[0]) if nxt else None}



# --- the book itself (EPUB) ------------------------------------------------------------------
# First Love Church holds distribution rights to the corpus (founder decision 2026-09-19), so members
# may read the whole book in the app and download it. Visibility rules apply exactly as for passages.

@router.get("/books/{source_id}/file", tags=["Passages"], summary="The book file (EPUB) for the in-app reader, or to download",
            responses={200: {"content": {"application/epub+zip": {}}}, 404: {"description": "Unknown, or a leaders-only book for a member"}})
def book_file(source_id: str, download: bool = False, user=Depends(verified_user), conn=Depends(db)):
    """Streams the stored EPUB. `?download=1` sets a filename so the browser saves it."""
    try:
        uuid.UUID(source_id)
    except ValueError:
        raise HTTPException(404, "not found")
    with transaction(conn):
        row = conn.execute(f"select s.file_uri, s.title from sources s where s.id = %s and {visibility_clause(user['role'])}",
                           (source_id,)).fetchone()
    if not row or not row[0].lower().endswith(".epub"):
        raise HTTPException(404, "not found")
    try:
        body, size = storage.open_book(row[0])
    except Exception:  # noqa: BLE001 - missing object in storage
        log.exception("book file %s missing from storage", source_id)
        raise HTTPException(404, "not found")
    headers = {"Content-Length": str(size), "Cache-Control": "private, max-age=3600"}
    if download:
        headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(row[1])}.epub"
    return StreamingResponse(body.iter_chunks(64 * 1024), media_type="application/epub+zip", headers=headers)
