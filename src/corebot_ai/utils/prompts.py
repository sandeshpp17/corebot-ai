"""Prompt-building utilities for the RAG pipeline."""

from __future__ import annotations


def build_rag_prompt(message: str, contexts: list[dict], history: list[dict]) -> str:
    """Compose a system prompt from user message, context, and history."""
    history_block = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history)
    context_block = "\n\n".join(
        f"Source: {c.get('source', 'unknown')}\n{c.get('content', '')}" for c in contexts
    )
    return (
        "You are Corebot-AI, a concise RAG assistant. "
        "Use only relevant context and cite sources by filename when possible.\n\n"
        f"Conversation History:\n{history_block}\n\n"
        f"Retrieved Context:\n{context_block}\n\n"
        f"User Question:\n{message}"
    )
