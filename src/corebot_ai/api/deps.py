"""Dependency providers for API routes."""

from __future__ import annotations

from functools import lru_cache

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


__all__ = ["get_db", "get_embedder", "get_llm"]
