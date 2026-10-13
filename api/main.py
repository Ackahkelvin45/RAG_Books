"""Admin portal + (later) chat API.  Run: uv run uvicorn api.main:app --reload --port 8000

/admin is protected by ADMIN_PASSWORD (session cookie). Pages are server-rendered.
"""
from __future__ import annotations

import hmac
import logging
import os
import shutil
import tempfile
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from shepherd import config, storage
from shepherd.db import connect, transaction
from worker.ingest import add_book, enqueue_reingest

from . import chat
from .chat import router as chat_router

DESCRIPTION = """
Answers from the books of Bishop Dag Heward-Mills, for members, shepherds and pastors.

### Trying it here
Sign-in uses a **session cookie**, so there is no token to paste. Call `POST /api/login`
(or `POST /api/signup`) with **Try it out**; every later call in this page then runs as that user.

### The sign-up journey
1. `POST /api/signup` → a 6-digit code is emailed
2. `POST /api/verify-email` with the code
3. `PUT /api/profile` → names, date of birth, member / shepherd / pastor (sends the welcome email)
4. `POST /api/ask` → streamed answer with citations; `GET /api/passages/{id}` opens a citation

`GET /api/me` tells you where a user is in that journey (`email_verified`, `profile_complete`).

### Two kinds of role
* **ministry_role** — what the person says they are. Shown to the AI. Grants nothing.
* **role** — access, set by an admin in the portal. `leader` and `admin` also see leaders-only books.
"""

TAGS = [
    {"name": "Auth", "description": "Email and password accounts, and the session cookie."},
    {"name": "Email verification", "description": "The 6-digit code emailed after every new sign-up, email or Google (sent with Resend)."},
    {"name": "Google sign-in", "description": "Browser redirects; test these by opening them in a browser tab, not with Try it out."},
    {"name": "Profile", "description": "One-time details collected after sign-up."},
    {"name": "Chat", "description": "Asking questions and past conversations. Requires a verified email."},
    {"name": "Passages", "description": "The passages that answers cite."},
    {"name": "Admin portal", "description": "Server-rendered HTML pages at /admin, protected by ADMIN_PASSWORD. Listed for reference; use them in the browser."},
]

log = logging.getLogger("api")
KEEP_WARM_SECONDS = int(os.environ.get("SHEPHERD_KEEP_WARM_SECONDS", "300"))   # 0 switches it off


def _warm_models(app_):
    """Load the embedding and reranking models at startup (~45 s), not on the first question,
    and keep touching them: on a small server the OS evicts their memory during quiet hours,
    and the next question paid ~60s to read them back (query_logs, 2026-10-13: 8s warm, 60s cold)."""
    import threading
    import time
    from contextlib import asynccontextmanager

    def touch():
        from shepherd.embed import get_embedder
        from shepherd.rerank import get_reranker
        get_embedder().embed(["keep warm"])          # one short forward pass reads every weight
        get_reranker().score("keep warm", ["keep warm"])

    def keep_warm():
        while True:
            time.sleep(KEEP_WARM_SECONDS)
            try:
                touch()
            except Exception:  # noqa: BLE001 - a failed ping must not kill the loop
                log.exception("keep-warm ping failed")

    @asynccontextmanager
    async def lifespan(_):
        import asyncio
        await asyncio.get_running_loop().run_in_executor(None, touch)
        if KEEP_WARM_SECONDS > 0:
            threading.Thread(target=keep_warm, name="keep-warm", daemon=True).start()
        yield
    return lifespan


app = FastAPI(title="First Love Church API", version="1.0", description=DESCRIPTION, openapi_tags=TAGS, lifespan=_warm_models(None),
              swagger_ui_parameters={"docExpansion": "list", "defaultModelsExpandDepth": 0, "tryItOutEnabled": True})
# behind Caddy (PUBLIC_URL is https) the cookie is marked Secure; locally it must not be, or the browser drops it
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "dev-only"),
                   https_only=os.environ.get("PUBLIC_URL", "").startswith("https://"))
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.include_router(chat_router)

ALLOWED = {".epub", ".pdf"}


def db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def admin(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


def page(request, name, **ctx):
    ctx["flash"] = request.session.pop("flash", None)
    return templates.TemplateResponse(request, name, ctx)


def flash(request, msg):
    request.session["flash"] = msg


# --- auth -----------------------------------------------------------------------

@app.get("/admin/login", tags=["Admin portal"], response_class=HTMLResponse)
def login_form(request: Request):
    return page(request, "login.html")


@app.post("/admin/login", tags=["Admin portal"])
def login(request: Request, password: str = Form(...)):
    expected = os.environ.get("ADMIN_PASSWORD", "")
    with connect() as conn, conn.transaction():
        if chat.login_locked(conn, "admin-portal"):
            flash(request, chat.LOCKED)
            return RedirectResponse("/admin/login", status_code=303)
        # an unset ADMIN_PASSWORD must never let an empty password in
        ok = bool(expected) and hmac.compare_digest(password.encode(), expected.encode())
        chat.record_login(conn, "admin-portal", ok)
    if not ok:
        flash(request, "Wrong password.")
        return RedirectResponse("/admin/login", status_code=303)
    request.session["admin"] = True
    return RedirectResponse("/admin/books", status_code=303)


@app.post("/admin/logout", tags=["Admin portal"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)




# --- books ----------------------------------------------------------------------

@app.get("/admin/books", tags=["Admin portal"], response_class=HTMLResponse, dependencies=[Depends(admin)])
def books(request: Request, conn=Depends(db)):
    with transaction(conn):
        rows = conn.execute("""
            select s.id, s.title, s.author, s.series, s.visibility, s.status, s.version, s.failure_reason,
                   (select count(*) from chunks c where c.source_id = s.id) as chunks,
                   coalesce(s.meta->>'needs_review', 'false') = 'true' as needs_review, s.created_at, p.message
            from sources s left join ingest_progress p on p.source_id = s.id
            where s.status <> 'superseded' order by s.created_at desc""").fetchall()
        queue = conn.execute("select count(*) filter (where status='pending'), count(*) filter (where status='processing') from sources").fetchone()
    return page(request, "books.html", books=rows, pending=queue[0], processing=queue[1])


@app.post("/admin/books", tags=["Admin portal"], dependencies=[Depends(admin)])
def upload(request: Request, file: UploadFile, title: str = Form(""), author: str = Form(""),
           series: str = Form(""), visibility: str = Form("member"), conn=Depends(db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        flash(request, f"Only EPUB and PDF files are accepted (got {suffix or 'no extension'}).")
        return RedirectResponse("/admin/books", status_code=303)
    if visibility not in ("member", "leader"):
        raise HTTPException(400, "bad visibility")
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / Path(file.filename).name
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        add_book(conn, dest, title.strip() or None, author.strip() or None, series.strip() or None, visibility)
    flash(request, f"Uploaded {file.filename}. The worker will process it shortly.")
    return RedirectResponse("/admin/books", status_code=303)


@app.post("/admin/books/{source_id}/reingest", tags=["Admin portal"], dependencies=[Depends(admin)])
def reingest(request: Request, source_id: str, conn=Depends(db)):
    try:
        enqueue_reingest(conn, source_id)
        flash(request, "Re-processing queued.")
    except LookupError as e:
        flash(request, str(e))
    return RedirectResponse("/admin/books", status_code=303)


@app.post("/admin/books/{source_id}/visibility", tags=["Admin portal"], dependencies=[Depends(admin)])
def set_visibility(request: Request, source_id: str, visibility: str = Form(...), conn=Depends(db)):
    if visibility not in ("member", "leader"):
        raise HTTPException(400, "bad visibility")
    with transaction(conn):
        conn.execute("update sources set visibility = %s where id = %s", (visibility, source_id))
    return RedirectResponse("/admin/books", status_code=303)


@app.post("/admin/books/{source_id}/reviewed", tags=["Admin portal"], dependencies=[Depends(admin)])
def mark_reviewed(request: Request, source_id: str, conn=Depends(db)):
    with transaction(conn):
        conn.execute("update sources set meta = meta - 'needs_review' where id = %s", (source_id,))
    return RedirectResponse("/admin/books", status_code=303)


@app.post("/admin/books/{source_id}/delete", tags=["Admin portal"], dependencies=[Depends(admin)])
def delete_book(request: Request, source_id: str, conn=Depends(db)):
    with transaction(conn):
        row = conn.execute("delete from sources where id = %s returning file_uri, title", (source_id,)).fetchone()
    if row:
        try:
            storage.delete(row[0])
        except Exception:  # noqa: BLE001 - the DB row is gone; an orphan file is harmless
            pass
        flash(request, f"Deleted {row[1]}.")
    return RedirectResponse("/admin/books", status_code=303)


# --- users ----------------------------------------------------------------------

ROLES = ("member", "leader", "admin")


@app.get("/admin/users", tags=["Admin portal"], response_class=HTMLResponse, dependencies=[Depends(admin)])
def users(request: Request, conn=Depends(db)):
    with transaction(conn):
        rows = conn.execute("""
            select u.id, u.email, u.name, u.role, u.created_at,
                   (select count(*) from conversations c where c.user_id = u.id) as chats,
                   u.ministry_role, u.date_of_birth, u.google_sub is not null
            from users u order by u.created_at desc""").fetchall()
    return page(request, "users.html", users=rows, roles=ROLES)


@app.post("/admin/users", tags=["Admin portal"], dependencies=[Depends(admin)])
def add_user(request: Request, email: str = Form(...), name: str = Form(""), role: str = Form("member"), conn=Depends(db)):
    if role not in ROLES or "@" not in email:
        raise HTTPException(400, "bad input")
    try:
        with transaction(conn):
            conn.execute("insert into users (email, name, role) values (%s, %s, %s)", (email.strip().lower(), name.strip() or None, role))
        flash(request, f"Added {email}.")
    except psycopg.errors.UniqueViolation:
        flash(request, f"{email} already exists.")
    return RedirectResponse("/admin/users", status_code=303)


@app.post("/admin/users/{user_id}/role", tags=["Admin portal"], dependencies=[Depends(admin)])
def set_role(request: Request, user_id: str, role: str = Form(...), conn=Depends(db)):
    if role not in ROLES:
        raise HTTPException(400, "bad role")
    with transaction(conn):
        conn.execute("update users set role = %s where id = %s", (role, user_id))
    return RedirectResponse("/admin/users", status_code=303)


@app.post("/admin/users/{user_id}/delete", tags=["Admin portal"], dependencies=[Depends(admin)])
def delete_user(request: Request, user_id: str, conn=Depends(db)):
    with transaction(conn):
        conn.execute("delete from messages where conversation_id in (select id from conversations where user_id = %s)", (user_id,))
        conn.execute("delete from conversations where user_id = %s", (user_id,))
        conn.execute("update query_logs set user_id = null where user_id = %s", (user_id,))
        conn.execute("delete from users where id = %s", (user_id,))
    flash(request, "User removed.")
    return RedirectResponse("/admin/users", status_code=303)


# --- activity -------------------------------------------------------------------

@app.get("/admin/activity", tags=["Admin portal"], response_class=HTMLResponse, dependencies=[Depends(admin)])
def activity(request: Request, conn=Depends(db)):
    with transaction(conn):
        totals = conn.execute("""
            select classification, count(*) from query_logs
            where created_at > now() - interval '30 days' group by 1 order by 2 desc""").fetchall()
        recent = conn.execute("""
            select q.created_at, u.email, q.classification, q.language, left(q.question, 120), left(q.answer, 160)
            from query_logs q left join users u on u.id = q.user_id order by q.created_at desc limit 50""").fetchall()
    return page(request, "activity.html", totals=totals, recent=recent, models=(config.GEN_MODEL, config.EMBED_MODEL, config.RERANK_MODEL))


# --- React app (production build) -----------------------------------------------
# In development Vite serves web/ on :5173 and proxies /api here. After `npm run build`
# this serves web/dist, with every non-API path falling back to index.html (client routing).
_DIST = Path(__file__).parent.parent / "web" / "dist"
if _DIST.exists():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = _DIST / path
        return FileResponse(f if path and f.is_file() else _DIST / "index.html")
