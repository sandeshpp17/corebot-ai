from __future__ import annotations

from functools import lru_cache

from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.backends.ollama import OllamaEmbedder, OllamaLLM
from corebot_ai.config import settings
from corebot_ai.database import get_db


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return OllamaEmbedder(
        settings.ollama_embed_model,
        settings.ollama_base_url,
        settings.ollama_timeout_sec,
    )


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    return OllamaLLM(
        settings.ollama_chat_model,
        settings.ollama_base_url,
        settings.embedding_dim,
        settings.ollama_timeout_sec,
    )


__all__ = ["get_db", "get_embedder", "get_llm"]
