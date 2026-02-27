"""Chat API routes and request/response schemas."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from ollama import ResponseError
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from corebot_ai.api.deps import get_db, get_embedder, get_llm, require_api_key
from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.config import settings
from corebot_ai.rag.pipeline import rag_chat

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_api_key)])


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

    message: str = Field(min_length=1)
    history: list[dict] = Field(default_factory=list)


class SourceItem(BaseModel):
    """Source snippet metadata in chat responses."""

    content: str
    source: str
    score: float


class ChatResponse(BaseModel):
    """Chat response payload."""

    reply: str
    sources: list[SourceItem]
    context_used: int


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    llm: LLM = Depends(get_llm),
) -> dict:
    """Return an assistant reply for a user message."""
    if len(request.message) > settings.max_message_chars:
        raise HTTPException(
            status_code=422,
            detail=f"Message too long. Max allowed is {settings.max_message_chars} characters.",
        )
    if len(request.history) > settings.max_history_messages:
        raise HTTPException(
            status_code=422,
            detail=f"History too large. Max allowed is {settings.max_history_messages} entries.",
        )
    try:
        return await rag_chat(request.message, request.history, embedder, llm, db)
    except ResponseError as exc:
        error_text = str(exc).lower()
        if "not found" in error_text:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Required Ollama model is missing. Expected chat model "
                    f'"{settings.ollama_chat_model}" and embedding model '
                    f'"{settings.ollama_embed_model}".'
                ),
            ) from exc
        raise HTTPException(status_code=503, detail=f"Ollama error: {exc}") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Database/vector schema mismatch. Ensure EMBEDDING_DIM matches the model "
                "and recreate DB tables."
            ),
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Chat request timed out while waiting for Ollama.",
        ) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Chat request timed out while waiting for Ollama.",
        ) from exc
