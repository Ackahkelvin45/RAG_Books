"""Embedding backends. `get_embedder()` returns the pinned bge-m3 model, or a
deterministic fake when SHEPHERD_EMBEDDER=fake (tests, CI)."""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from typing import Protocol, Sequence

from . import config


class Embedder(Protocol):
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
    def count_tokens(self, text: str) -> int: ...


class FakeEmbedder:
    """Stable pseudo-vectors from a hash. Similar texts are NOT similar; fine for plumbing tests."""

    dim = config.EMBED_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out = []
        for t in texts:
            h = hashlib.sha256(t.encode()).digest()
            vec = [((h[i % 32] / 255.0) - 0.5) for i in range(self.dim)]
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            out.append([v / norm for v in vec])
        return out

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class BgeM3Embedder:
    dim = config.EMBED_DIM

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        # bge-m3 only: load the pytorch_model.bin weights so the hub does not also fetch the
        # 2.2 GB safetensors copy (matters on slow links). Smaller models ship one copy.
        kwargs = {"use_safetensors": False} if "bge-m3" in config.EMBED_MODEL else {}
        self.model = SentenceTransformer(config.EMBED_MODEL, device=config.device(), model_kwargs=kwargs)
        self.tokenizer = self.model.tokenizer

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vecs = self.model.encode(
            list(texts), batch_size=8, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vecs]

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    if os.environ.get("SHEPHERD_EMBEDDER", "").lower() == "fake":
        return FakeEmbedder()
    return BgeM3Embedder()
