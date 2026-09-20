"""Outgoing email via Resend (https://resend.com). Without RESEND_API_KEY the message is
written to the log instead, so sign-up can be tested locally.

RESEND_API_KEY=re_...   MAIL_FROM="First Love Church <no-reply@your-verified-domain>"
(Until a domain is verified in Resend, only onboarding@resend.dev works, and only to your own address.)
"""
from __future__ import annotations

import logging
import os

import httpx

log = logging.getLogger("mail")


def send(to: str, subject: str, body: str, html: str | None = None) -> None:
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        log.warning("RESEND_API_KEY not set; email to %s not sent.", to)
        print(f"\n[DEV EMAIL to {to}] {subject}\n{body}\n", flush=True)
        return
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {key}"},
        json={"from": os.environ.get("MAIL_FROM", "First Love Church <onboarding@resend.dev>"),
              "to": [to], "subject": subject, "text": body, **({"html": html} if html else {})},
        timeout=15,
    )
    if r.status_code >= 400:
        log.error("Resend rejected email to %s: %s %s", to, r.status_code, r.text[:300])
        r.raise_for_status()
