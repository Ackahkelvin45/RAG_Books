"""Contextual header prepended to each chunk before embedding (handoff 4d)."""
from __future__ import annotations


def context_header(
    title: str,
    author: str | None,
    series: str | None,
    chapter: int | None,
    chapter_title: str | None,
) -> str:
    parts = [f"From {title}"]
    if author:
        parts.append(f"by {author}")
    if series:
        parts.append(f"({series})")
    head = " ".join(parts) + "."
    if chapter is not None and chapter_title:
        head += f" Chapter {chapter}: {chapter_title}."
    elif chapter is not None:
        head += f" Chapter {chapter}."
    elif chapter_title:
        head += f" {chapter_title}."
    return head


def enrich(raw: str, header: str) -> str:
    return f"{header}\n\n{raw}"
