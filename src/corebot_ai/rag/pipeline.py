"""RAG pipeline orchestration."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.config import settings
from corebot_ai.retrieval.pgvector import retrieve
from corebot_ai.utils.prompts import build_rag_prompt

logger = logging.getLogger(__name__)


async def rag_chat(
    message: str,
    history: list[dict],
    embedder: Embedder,
    llm: LLM,
    db: Session,
) -> dict:
    """Generate a response using retrieval-augmented generation."""
    contexts: list[dict] = []
    try:
        contexts = await retrieve(
            query=message,
            embedder=embedder,
            db=db,
            top_k=settings.retrieve_top_k,
            min_score=settings.retrieve_min_score,
        )
    except Exception as exc:
        # Keep chat available even when retrieval or embeddings fail.
        logger.warning("Retrieval failed; continuing without RAG context: %s", exc)

    prompt = build_rag_prompt(message=message, contexts=contexts, history=history[-3:])
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ]
    reply = await llm.chat(messages)

    return {
        "reply": reply,
        "sources": [
            {"content": str(c["content"])[:100], "source": c["source"], "score": c["score"]}
            for c in contexts
        ],
        "context_used": len(contexts),
    }
