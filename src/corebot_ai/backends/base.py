from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Embedder(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LLM(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict[str, Any]], tools: list | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_embedding_dim(self) -> int:
        raise NotImplementedError
