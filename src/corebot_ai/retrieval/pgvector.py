"""pgvector-based semantic retrieval implementation."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from corebot_ai.backends.base import Embedder


async def retrieve(
    query: str,
    embedder: Embedder,
    db: Session,
    top_k: int = 5,
    min_score: float = 0.7,
) -> list[dict[str, str | float]]:
    """Retrieve top matching chunks for a query."""
    query_emb = (await embedder.embed([query]))[0]
    vector_literal = "[" + ",".join(str(x) for x in query_emb) + "]"

    result = db.execute(
        text(
            """
            SELECT
                dc.content,
                d.filename,
                1 - (dc.embedding <=> CAST(:query_emb AS vector)) as score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE 1 - (dc.embedding <=> CAST(:query_emb AS vector)) > :min_score
            ORDER BY dc.embedding <=> CAST(:query_emb AS vector)
            LIMIT :top_k
            """
        ),
        {"query_emb": vector_literal, "top_k": top_k, "min_score": min_score},
    ).fetchall()

    return [{"content": r.content, "source": r.filename, "score": float(r.score)} for r in result]
