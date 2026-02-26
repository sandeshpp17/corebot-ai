from __future__ import annotations

import asyncio
from typing import Any

from ollama import AsyncClient

from corebot_ai.backends.base import Embedder, LLM


class OllamaEmbedder(Embedder):
    def __init__(self, model: str, base_url: str, timeout_sec: int = 120) -> None:
        self.model = model
        self.timeout_sec = timeout_sec
        self.client = AsyncClient(host=base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            resp = await asyncio.wait_for(
                self.client.embeddings(model=self.model, prompt=text), timeout=self.timeout_sec
            )
            results.append(resp["embedding"])
        return results


class OllamaLLM(LLM):
    def __init__(self, model: str, base_url: str, embedding_dim: int, timeout_sec: int = 120) -> None:
        self.model = model
        self.embedding_dim = embedding_dim
        self.timeout_sec = timeout_sec
        self.client = AsyncClient(host=base_url)

    async def chat(self, messages: list[dict[str, Any]], tools: list | None = None) -> str:
        resp = await asyncio.wait_for(
            self.client.chat(model=self.model, messages=messages, tools=tools), timeout=self.timeout_sec
        )
        return resp["message"]["content"]

    def get_embedding_dim(self) -> int:
        return self.embedding_dim
