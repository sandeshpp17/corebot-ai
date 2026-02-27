"""Ollama backend implementations for embeddings and chat."""

from __future__ import annotations

import asyncio
from typing import Any

from ollama import AsyncClient

from corebot_ai.backends.base import Embedder, LLM


class OllamaEmbedder(Embedder):
    """Embedder implementation backed by Ollama."""

    def __init__(
        self,
        model: str,
        base_url: str,
        timeout_sec: int = 120,
        concurrency: int = 4,
    ) -> None:
        """Initialize embedder with model name, host, and timeout."""
        self.model = model
        self.timeout_sec = timeout_sec
        self.concurrency = max(1, concurrency)
        self.client = AsyncClient(host=base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed each text input using the configured Ollama model."""
        semaphore = asyncio.Semaphore(self.concurrency)

        async def _embed_one(text: str) -> list[float]:
            async with semaphore:
                resp = await asyncio.wait_for(
                    self.client.embeddings(model=self.model, prompt=text), timeout=self.timeout_sec
                )
                return resp["embedding"]

        tasks = [_embed_one(text) for text in texts]
        results = await asyncio.gather(*tasks)
        return list(results)


class OllamaLLM(LLM):
    """LLM implementation backed by Ollama chat API."""

    def __init__(self, model: str, base_url: str, embedding_dim: int, timeout_sec: int = 120) -> None:
        """Initialize chat model with host, embedding dim, and timeout."""
        self.model = model
        self.embedding_dim = embedding_dim
        self.timeout_sec = timeout_sec
        self.client = AsyncClient(host=base_url)

    async def chat(self, messages: list[dict[str, Any]], tools: list | None = None) -> str:
        """Generate assistant response text from chat messages."""
        resp = await asyncio.wait_for(
            self.client.chat(model=self.model, messages=messages, tools=tools), timeout=self.timeout_sec
        )
        return resp["message"]["content"]

    def get_embedding_dim(self) -> int:
        """Return embedding dimension configured for this backend."""
        return self.embedding_dim
