"""Scope classifier, run before retrieval.

  off_scope  -> polite decline.
  sensitive  -> answered like any other question (users are shepherds), but the
                category is logged and a short safety line is appended for
                life-at-risk topics.
  answerable -> retrieve.
  Any error or unparseable output -> answerable with category 'unknown' (the
  question still goes to the books; nothing is lost by answering).

An English lexicon flags crisis phrases regardless of the model. (Twi deferred: founder call 2026-09-19.)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from . import config, llm

log = logging.getLogger("classify")

PROMPT_VERSION = "classifier_v4"

# ponytail: English only for now; extend from real query logs. Twi list deferred until wanted.
LEXICON = {
    "self_harm": [
        "kill myself", "kill herself", "kill himself", "kill themselves", "end my life", "end her life",
        "end his life", "suicide", "suicidal", "want to die", "wants to die", "don't want to live",
    ],
    "abuse": ["beats me", "beats her", "beats him", "hits me", "raped", "molest", "abusing"],
    "crisis": ["overdose", "no reason to live"],
}
_LEX = [(cat, p.lower()) for cat, ps in LEXICON.items() for p in ps]
LAST_ANSWER_CHARS = 400     # enough for the classifier to resolve "they"/"it" in a follow-up
SAFETY_CATEGORIES = {"self_harm", "abuse", "crisis", "mental_health"}

SYSTEM = """You classify questions sent to a church book-search tool used by pastors and shepherds. Reply with JSON only:
{"label": "answerable" | "sensitive" | "off_scope" | "help" | "chat", "category": string|null, "language": "en" | "tw" | "mixed", "search": string (only when earlier questions are listed)}

- sensitive: the question concerns self-harm or suicide, abuse (domestic, child, sexual), acute mental-health crisis, severe marital crisis, or financial desperation, whether the asker's own or someone they are caring for.
- off_scope: not about Christian faith, the Bible, church life, ministry, or the church's teaching (e.g. sports, coding, politics trivia).
- help: the person asks about this tool itself: what it can do, what to ask it, how to use it, who made it.
- chat: a greeting, thanks, goodbye or small talk with no question in it ("hi", "good morning", "thank you", "God bless you").
- answerable: everything else a church library could speak to.
category: for sensitive, one of self_harm, abuse, mental_health, marital_crisis, financial, other; else null.
language: en, tw (Twi), or mixed.
If the input lists earlier questions, classify ONLY the "Current question". Use the earlier ones just to understand a follow-up (e.g. "and how do they get out?" after a question about a book is answerable).
When earlier questions are listed, also return "search": the current question rewritten to stand on its own, for searching the books. Replace words like "they", "it", "that" with what they refer to. If the current question starts a new topic or already stands alone, return it unchanged; never carry an old topic into a new one. Keep it one short question."""


@dataclass
class Verdict:
    label: str            # answerable | sensitive | off_scope | help | chat
    category: str | None
    language: str
    source: str           # lexicon | model | fallback
    search: str | None = None   # follow-up rewritten as a standalone question (model, follow-ups only)


def lexicon_hit(question: str) -> str | None:
    q = question.lower()
    return next((cat for cat, phrase in _LEX if phrase in q), None)


def classify(question: str, earlier: list[str] = (), last_answer: str | None = None) -> Verdict:
    if cat := lexicon_hit(question):          # current question only: one crisis turn must not flag every later one
        return Verdict("sensitive", cat, "en", "lexicon")
    content = question if not earlier else (
        "Earlier questions in this conversation:\n" + "\n".join(f"- {q}" for q in earlier)
        + (f"\n\nStart of the last answer:\n{last_answer[:LAST_ANSWER_CHARS]}" if last_answer else "")
        + f"\n\nCurrent question: {question}")
    try:
        r = llm.client().chat.completions.create(
            model=config.CLASSIFIER_MODEL,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}],
            response_format={"type": "json_object"}, temperature=0, max_tokens=160,
        )
        d = json.loads(r.choices[0].message.content)
        label = d.get("label")
        if label not in ("answerable", "sensitive", "off_scope", "help", "chat"):
            raise ValueError(f"bad label {label!r}")
        lang = d.get("language") if d.get("language") in ("en", "tw", "mixed") else "en"
        search = d.get("search") if earlier and isinstance(d.get("search"), str) and d["search"].strip() else None
        return Verdict(label, d.get("category") if label == "sensitive" else None, lang, "model", search)
    except Exception as e:  # noqa: BLE001
        log.error("classifier failed: %s: %s", type(e).__name__, e)
        return Verdict("answerable", "unknown", "en", "fallback")
