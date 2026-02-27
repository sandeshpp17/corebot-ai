"""Dependency providers for API routes."""

from __future__ import annotations

import secrets
from functools import lru_cache

from fastapi import Header, HTTPException

from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.backends.ollama import OllamaEmbedder, OllamaLLM
from corebot_ai.config import settings
from corebot_ai.database import get_db


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Return cached embedder backend instance."""
    return OllamaEmbedder(
        settings.ollama_embed_model,
        settings.ollama_base_url,
        settings.ollama_timeout_sec,
        settings.ollama_embed_concurrency,
    )


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    """Return cached LLM backend instance."""
    return OllamaLLM(
        settings.ollama_chat_model,
        settings.ollama_base_url,
        settings.embedding_dim,
        settings.ollama_timeout_sec,
    )


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    """Reject requests missing a valid API key."""
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")


__all__ = ["get_db", "get_embedder", "get_llm", "require_api_key"]
