"""Chat API routes and request/response schemas."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from ollama import ResponseError
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from corebot_ai.api.deps import (
    get_db,
    get_diagnostic_provider,
    get_embedder,
    get_llm,
    require_api_key,
)
from corebot_ai.assistant.pipeline import assistant_chat
from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.config import settings
from corebot_ai.tools.base import DiagnosticToolProvider

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_api_key)])


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

    message: str = Field(min_length=1)
    history: list[dict] = Field(default_factory=list)
    mode: str = "auto"
    app_context: dict = Field(default_factory=dict)


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
    mode: str
    actions: list[str] = Field(default_factory=list)
    diagnostics_status: str | None = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    llm: LLM = Depends(get_llm),
    diagnostic_provider: DiagnosticToolProvider = Depends(get_diagnostic_provider),
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
        return await assistant_chat(
            message=request.message,
            history=request.history,
            mode=request.mode,
            app_context=request.app_context,
            embedder=embedder,
            llm=llm,
            db=db,
            diagnostic_provider=diagnostic_provider,
        )
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
