from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from ollama import ResponseError
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from corebot_ai.api.deps import get_db, get_embedder, get_llm
from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.config import settings
from corebot_ai.rag.pipeline import rag_chat

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict] = Field(default_factory=list)


class SourceItem(BaseModel):
    content: str
    source: str
    score: float


class ChatResponse(BaseModel):
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
