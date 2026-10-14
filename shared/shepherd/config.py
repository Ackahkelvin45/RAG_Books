"""Pinned models and environment-derived settings. One place to change them."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Pinned per handoff section 4f / 5 / 6. Changing EMBED_MODEL requires a full re-embed.
# bge-m3 is 2.2 GB resident and 2.7s per question on one core. A small server can run a
# smaller model instead: set all three together, and backfill the new column first with
# `python -m worker.reembed` - the two columns coexist, so switching back is one env change.
EMBED_MODEL = os.environ.get("SHEPHERD_EMBED_MODEL", "BAAI/bge-m3")
EMBED_DIM = int(os.environ.get("SHEPHERD_EMBED_DIM", "1024"))
EMBED_COLUMN = os.environ.get("SHEPHERD_EMBED_COLUMN", "embedding")
if EMBED_COLUMN not in ("embedding", "embedding_small", "embedding_base"):     # it is interpolated into SQL
    raise RuntimeError(f"SHEPHERD_EMBED_COLUMN must be embedding, embedding_small or embedding_base, not {EMBED_COLUMN!r}")
# Reranking is by far the slowest step on a CPU: 4.6s per passage for this 568M-parameter
# model on one core. SHEPHERD_RERANK_MODEL swaps in a smaller one; measure the cost with
# `python -m eval.run retrieval` before changing it on a live server.
RERANK_MODEL = os.environ.get("SHEPHERD_RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
# Reranking cost scales with the pool size AND with this window. Chunks are at most 500
# tokens, so the 1024 default never truncates in practice; lowering it saves nothing.
RERANK_MAX_LEN = int(os.environ.get("SHEPHERD_RERANK_MAX_LEN", "1024"))
# Where the models run: cpu on the server; a Mac with Apple silicon uses its GPU (mps, ~3x faster). SHEPHERD_DEVICE overrides.
RERANK_POOL = int(os.environ.get("SHEPHERD_RERANK_POOL", "20"))   # candidates reranked per question; the reranker is the slow step
# Written to query_logs.models and every eval run, so a number can always be traced to the models behind it.
MODELS = f"{EMBED_MODEL}@{EMBED_COLUMN}+{RERANK_MODEL}"


def device() -> str:
    forced = os.environ.get("SHEPHERD_DEVICE")
    if forced:
        return forced
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"
# DeepSeek, via its OpenAI-compatible API (founder decision 2026-09-18).
LLM_BASE_URL = "https://api.deepseek.com"
LLM_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
GEN_MODEL = "deepseek-chat"
CLASSIFIER_MODEL = "deepseek-chat"
JUDGE_MODEL = "deepseek-chat"

APP_DATABASE_URL = os.environ.get("APP_DATABASE_URL", "")
ADMIN_DATABASE_URL = os.environ.get("DATABASE_URL", "")
