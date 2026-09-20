"""One OpenAI-compatible client pointed at DeepSeek. Tests swap `client()` via monkeypatch."""
from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from . import config


@lru_cache(maxsize=1)
def client() -> OpenAI:
    if not config.LLM_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    return OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY, timeout=60, max_retries=2)
