"""Rerankers. `get_reranker()` returns the pinned bge-reranker-v2-m3 cross-encoder,
or a word-overlap fake when SHEPHERD_RERANKER=fake (tests, CI)."""
from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Protocol, Sequence

from . import config

_WORD = re.compile(r"[a-z0-9']+")


class Reranker(Protocol):
    def score(self, query: str, passages: Sequence[str]) -> list[float]: ...


class FakeReranker:
    """Fraction of query words present in the passage. Deterministic, no model."""

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        q = set(_WORD.findall(query.lower()))
        out = []
        for p in passages:
            words = set(_WORD.findall(p.lower()))
            out.append(len(q & words) / len(q) if q else 0.0)
        return out


class BgeReranker:
    def __init__(self) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(config.RERANK_MODEL, device=config.device(), max_length=1024)

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        scores = self.model.predict([(query, p) for p in passages], batch_size=8, show_progress_bar=False)
        return [float(s) for s in scores]


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    if os.environ.get("SHEPHERD_RERANKER", "").lower() == "fake":
        return FakeReranker()
    return BgeReranker()
