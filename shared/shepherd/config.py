"""Pinned models and environment-derived settings. One place to change them."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Pinned per handoff section 4f / 5 / 6. Changing EMBED_MODEL requires a full re-embed.
EMBED_MODEL = "BAAI/bge-m3"
EMBED_DIM = 1024
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
# Reranking cost scales with the pool size AND with this window. Chunks are at most 500
# tokens, so a small server can set SHEPHERD_RERANK_MAX_LEN=512 and truncate almost nothing.
RERANK_MAX_LEN = int(os.environ.get("SHEPHERD_RERANK_MAX_LEN", "1024"))
# Where the models run: cpu on the server; a Mac with Apple silicon uses its GPU (mps, ~3x faster). SHEPHERD_DEVICE overrides.
RERANK_POOL = int(os.environ.get("SHEPHERD_RERANK_POOL", "20"))   # candidates reranked per question; the reranker is the slow step


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
