"""Recursive, chapter-bounded chunking.

Paragraphs are packed into chunks of roughly `target` tokens, never exceeding
`max_tokens`. Overlap carries the tail of the previous chunk into the next so a
thought split across a boundary survives in at least one chunk. A chapter is
chunked on its own; nothing crosses chapter boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

TokenCounter = Callable[[str], int]

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
_PARA = re.compile(r"\n\s*\n")

TARGET, MAX_TOKENS, OVERLAP = 400, 500, 0.15
# A section's last few paragraphs used to become a chunk of their own however small (289 of 13,843 chunks
# were under 100 tokens; the smallest, a bare verse reference, was 4). A tail under this joins the previous chunk.
MIN_TAIL = 80


@dataclass
class Chunk:
    text: str
    token_count: int
    index: int


def whitespace_tokens(text: str) -> int:
    return len(text.split())


def _units(text: str, count: TokenCounter, max_tokens: int) -> list[tuple[str, int]]:
    """Paragraphs, with oversized paragraphs split into sentences."""
    units: list[tuple[str, int]] = []
    for para in _PARA.split(text):
        para = " ".join(para.split())
        if not para:
            continue
        n = count(para)
        if n <= max_tokens:
            units.append((para, n))
            continue
        for sent in _SENT.split(para):
            sent = sent.strip()
            if sent:
                units.append((sent, count(sent)))
    return units


def chunk_text(
    text: str,
    count: TokenCounter = whitespace_tokens,
    target: int = TARGET,
    max_tokens: int = MAX_TOKENS,
    overlap_ratio: float = OVERLAP,
    min_tail: int = MIN_TAIL,
) -> list[Chunk]:
    units = _units(text, count, max_tokens)
    chunks: list[Chunk] = []
    cur: list[tuple[str, int]] = []
    cur_n = 0
    carried = 0          # how many leading units of `cur` are overlap copied from the previous chunk

    def flush() -> None:
        nonlocal cur, cur_n, carried
        if not cur:
            return
        body = "\n\n".join(u for u, _ in cur)
        chunks.append(Chunk(body, count(body), len(chunks)))
        # keep the trailing units worth ~overlap_ratio of this chunk
        keep: list[tuple[str, int]] = []
        keep_n = 0
        budget = int(cur_n * overlap_ratio)
        for u in reversed(cur):
            if keep_n + u[1] > budget:
                break
            keep.insert(0, u)
            keep_n += u[1]
        if not keep and budget > 0:
            # last unit is bigger than the budget: carry its trailing sentences instead
            tail: list[str] = []
            for sent in reversed(_SENT.split(cur[-1][0])):
                n = count(sent)
                if keep_n + n > budget:
                    break
                tail.insert(0, sent)
                keep_n += n
            if tail:
                keep = [(" ".join(tail), keep_n)]
        cur, cur_n, carried = keep, keep_n, len(keep)

    for unit, n in units:
        if cur and cur_n + n > max_tokens:
            flush()
        cur.append((unit, n))
        cur_n += n
        if cur_n >= target:
            flush()
    # the tail: whatever arrived after the last flush (the carried overlap alone is nothing new)
    new = cur[carried:]
    if new:
        new_n = sum(n for _, n in new)
        if chunks and new_n < min_tail and chunks[-1].token_count + new_n <= max_tokens + min_tail:
            prev = chunks[-1]
            text = prev.text + "\n\n" + "\n\n".join(u for u, _ in new)
            chunks[-1] = Chunk(text, count(text), prev.index)
        else:
            body = "\n\n".join(u for u, _ in cur)
            chunks.append(Chunk(body, count(body), len(chunks)))
    return chunks
