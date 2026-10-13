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

        self.model = CrossEncoder(config.RERANK_MODEL, device=config.device(), max_length=config.RERANK_MAX_LEN)
        # Never ask a model for more tokens than it has positions: MiniLM stops at 512, and a
        # merged neighbour passage can exceed that, which crashes the whole answer mid-request.
        limit = getattr(self.model.model.config, "max_position_embeddings", config.RERANK_MAX_LEN)
        self.model.max_length = min(config.RERANK_MAX_LEN, limit)

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
