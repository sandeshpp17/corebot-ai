"""SQLAlchemy ORM models for documents and embedded chunks."""

from __future__ import annotations

from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from corebot_ai.config import settings


class Base(DeclarativeBase):
    """Base ORM class for all database models."""

    pass


class Document(Base):
    """Metadata for an ingested document."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    meta_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all,delete")


class DocumentChunk(Base):
    """Chunked document content and its embedding vector."""

    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")


# pgvector ivfflat cannot index vectors with > 2000 dimensions.
if settings.embedding_dim <= 2000:
    Index("ix_document_chunks_embedding", DocumentChunk.embedding, postgresql_using="ivfflat")
Index("ix_document_chunks_doc_chunk", DocumentChunk.document_id, DocumentChunk.chunk_index, unique=True)
