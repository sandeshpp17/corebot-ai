from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.orm import Session

from corebot_ai.backends.base import Embedder
from corebot_ai.config import settings
from corebot_ai.ingestion.formats import extract_text
from corebot_ai.models import Document, DocumentChunk


def smart_chunk(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []

    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


async def ingest_pipeline(
    filename: str,
    content: bytes,
    mime_type: str,
    db: Session,
    embedder: Embedder,
) -> UUID:
    text = await extract_text(content, mime_type)
    chunks = smart_chunk(text, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)

    doc = Document(filename=filename, mime_type=mime_type, meta_json=json.dumps({"chunks": len(chunks)}))
    db.add(doc)
    db.flush()

    if chunks:
        embeddings = await embedder.embed(chunks)
        if embeddings:
            actual_dim = len(embeddings[0])
            if actual_dim != settings.embedding_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: model produced {actual_dim}, "
                    f"but EMBEDDING_DIM is {settings.embedding_dim}. "
                    "Update EMBEDDING_DIM and recreate vector tables."
                )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=False)):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk,
                    embedding=emb,
                )
            )

    db.commit()
    return doc.id
