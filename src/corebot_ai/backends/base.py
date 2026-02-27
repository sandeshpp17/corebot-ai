"""Abstract interfaces for embedding and chat backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Embedder(ABC):
    """Interface for text embedding providers."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for input texts."""
        raise NotImplementedError


class LLM(ABC):
    """Interface for chat-capable language models."""

    @abstractmethod
    async def chat(self, messages: list[dict[str, Any]], tools: list | None = None) -> str:
        """Generate a chat response from messages."""
        raise NotImplementedError

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Return embedding dimension expected by this backend."""
        raise NotImplementedError
