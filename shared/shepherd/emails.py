"""Email templates. Each returns (subject, text, html).

HTML is table-based with inline styles (what Gmail/Outlook reliably render) and uses no
images, so nothing is blocked or needs hosting. Colours follow the web app.
"""
from __future__ import annotations

import os
from html import escape

APP_NAME = "First Love Church"
INK, SLATE, MUTED, ACCENT = "#1c1422", "#5b6477", "#7a8193", "#7b4fb8"


def _app_url() -> str:
    return os.environ.get("PUBLIC_URL", "http://localhost:8010").rstrip("/")


def _layout(preheader: str, body_html: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{APP_NAME}</title></head>
<body style="margin:0;padding:0;background:#f6f1fa;">
<span style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(160deg,#fdfbfd 0%,#f7e6f5 55%,#e7e0fa 100%);background-color:#f6f1fa;">
<tr><td align="center" style="padding:40px 16px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">
    <tr><td align="center" style="padding-bottom:20px;font-family:Manrope,Segoe UI,Helvetica,Arial,sans-serif;">
      <div style="font-size:34px;line-height:1;color:{INK};">&#10022;&#10022;</div>
      <div style="margin-top:10px;font-size:20px;color:{INK};letter-spacing:-.01em;">{APP_NAME}</div>
    </td></tr>
    <tr><td style="background:#ffffff;border:1px solid #ece4f5;border-radius:12px;padding:32px 28px;font-family:Manrope,Segoe UI,Helvetica,Arial,sans-serif;color:#1f2330;font-size:15px;line-height:1.6;">
      {body_html}
    </td></tr>
    <tr><td align="center" style="padding-top:20px;font-family:Manrope,Segoe UI,Helvetica,Arial,sans-serif;font-size:12px;color:{MUTED};line-height:1.6;">
      Answers from the books of Bishop Dag Heward-Mills.<br>
      Powered by <a href="https://dagbooks.org/" style="color:{ACCENT};text-decoration:none;font-weight:600;">Dag Books</a>
    </td></tr>
  </table>
</td></tr></table></body></html>"""


def otp_email(code: str, minutes: int) -> tuple[str, str, str]:
    subject = f"Your {APP_NAME} code: {code}"
    text = (f"Your verification code is {code}\n\nIt expires in {minutes} minutes.\n"
            "If you did not sign up, you can ignore this email.\n\n— " + APP_NAME)
    spaced = "&nbsp;".join(escape(code))
    html = _layout(f"Your code is {code}", f"""
      <h1 style="margin:0 0 8px;font-size:22px;font-weight:600;color:{INK};">Confirm your email</h1>
      <p style="margin:0 0 24px;color:{SLATE};">Enter this code in the app to finish creating your account.</p>
      <div style="text-align:center;background:linear-gradient(90deg,#eadcf8,#f1eafb);background-color:#efe6fa;border-radius:10px;padding:22px 12px;">
        <div style="font-size:36px;font-weight:700;letter-spacing:6px;color:{INK};font-family:'SF Mono',Menlo,Consolas,monospace;">{spaced}</div>
      </div>
      <p style="margin:24px 0 0;color:{SLATE};font-size:14px;">This code expires in <strong>{minutes} minutes</strong>. If you did not sign up, you can safely ignore this email.</p>""")
    return subject, text, html


_ROLE_LINE = {
    "pastor": "As a pastor, you can bring the questions of ministry and leadership to Bishop Dag's books.",
    "shepherd": "As a shepherd, you can find what Bishop Dag's books say for the people you care for.",
    "member": "Whatever you are walking through, you can find what Bishop Dag's books say about it.",
}


def welcome_email(first_name: str, ministry_role: str | None) -> tuple[str, str, str]:
    name = first_name.strip() or "friend"
    url = _app_url()
    role_line = _ROLE_LINE.get(ministry_role or "", _ROLE_LINE["member"])
    examples = ["How can I overcome fear and discouragement?",
                "How do I know if someone is becoming disloyal?",
                "What do his books say about Romans 8:28?"]
    subject = f"Welcome to {APP_NAME}, {name}"
    text = (f"Welcome, {name}!\n\nYour account is ready. {role_line}\n\n"
            "Ask anything, and every answer comes from the books of Bishop Dag Heward-Mills, "
            "with the book and chapter it comes from so you can read it for yourself.\n\n"
            "Try asking:\n" + "\n".join(f"- {q}" for q in examples) + f"\n\nStart here: {url}\n\n— {APP_NAME}")
    items = "".join(
        f'<tr><td style="padding:0 0 8px;"><div style="background:#f7f2fc;border:1px solid #ece4f5;border-radius:8px;padding:10px 14px;color:#1f2330;">{escape(q)}</div></td></tr>'
        for q in examples)
    html = _layout(f"Your account is ready, {name}.", f"""
      <h1 style="margin:0 0 8px;font-size:22px;font-weight:600;color:{INK};">Welcome, {escape(name)}!</h1>
      <p style="margin:0 0 14px;color:{SLATE};">Your account is ready. {escape(role_line)}</p>
      <p style="margin:0 0 22px;color:{SLATE};">Ask anything, and every answer comes from the books of Bishop Dag Heward-Mills, with the book and chapter it comes from so you can read it for yourself.</p>
      <p style="margin:0 0 10px;font-weight:600;color:{SLATE};font-size:14px;">Try asking</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{items}</table>
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:22px;"><tr>
        <td style="border-radius:8px;background:{INK};"><a href="{escape(url)}" style="display:inline-block;padding:12px 22px;color:#ffffff;text-decoration:none;font-weight:600;font-size:15px;">Start asking</a></td>
      </tr></table>""")
    return subject, text, html
