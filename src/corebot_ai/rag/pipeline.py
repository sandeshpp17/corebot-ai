"""RAG pipeline orchestration."""

from __future__ import annotations

import hashlib
import json
import logging

from sqlalchemy.orm import Session

from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.cache import get_cache
from corebot_ai.config import settings
from corebot_ai.retrieval.pgvector import retrieve
from corebot_ai.utils.prompts import build_rag_prompt

logger = logging.getLogger(__name__)


def _cache_key(prefix: str, payload: dict) -> str:
    """Generate deterministic cache key from JSON payload."""
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"corebot:{prefix}:{digest}"


async def rag_chat(
    message: str,
    history: list[dict],
    embedder: Embedder,
    llm: LLM,
    db: Session,
) -> dict:
    """Generate a response using retrieval-augmented generation."""
    cache = get_cache()
    short_history = history[-3:]
    retrieval_key = _cache_key("retrieval", {"message": message})
    response_key = _cache_key("response", {"message": message, "history": short_history})

    cached_response = cache.get(response_key)
    if cached_response is not None:
        return cached_response

    contexts: list[dict] = []
    try:
        cached_contexts = cache.get(retrieval_key)
        if cached_contexts is None:
            contexts = await retrieve(
                query=message,
                embedder=embedder,
                db=db,
                top_k=settings.retrieve_top_k,
                min_score=settings.retrieve_min_score,
            )
            cache.set(retrieval_key, {"contexts": contexts}, settings.cache_ttl_sec)
        else:
            contexts = list(cached_contexts.get("contexts", []))
    except Exception as exc:
        # Keep chat available even when retrieval or embeddings fail.
        logger.warning("Retrieval failed; continuing without RAG context: %s", exc)

    prompt = build_rag_prompt(message=message, contexts=contexts, history=short_history)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ]
    reply = await llm.chat(messages)

    result = {
        "reply": reply,
        "sources": [
            {"content": str(c["content"])[:100], "source": c["source"], "score": c["score"]}
            for c in contexts
        ],
        "context_used": len(contexts),
    }
    cache.set(response_key, result, settings.cache_ttl_sec)
    return result
