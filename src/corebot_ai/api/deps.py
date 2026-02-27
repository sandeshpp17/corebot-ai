"""Dependency providers for API routes."""

from __future__ import annotations

import secrets
from functools import lru_cache

from fastapi import Header, HTTPException

from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.backends.ollama import OllamaEmbedder, OllamaLLM
from corebot_ai.config import settings
from corebot_ai.database import get_db
from corebot_ai.tools import DiagnosticToolProvider, NullDiagnosticToolProvider, WebAppDiagnosticToolProvider


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


@lru_cache(maxsize=1)
def get_diagnostic_provider() -> DiagnosticToolProvider:
    """Return configured diagnostics provider for incident mode."""
    if settings.webapp_tools_enabled and settings.webapp_diagnostics_base_url:
        return WebAppDiagnosticToolProvider(
            settings.webapp_diagnostics_base_url,
            settings.webapp_diagnostics_token,
        )
    return NullDiagnosticToolProvider()


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    """Reject requests missing a valid API key when key auth is enabled."""
    if not settings.api_key.strip():
        return
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")


__all__ = ["get_db", "get_embedder", "get_llm", "get_diagnostic_provider", "require_api_key"]
