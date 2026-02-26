from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from ollama import ResponseError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from corebot_ai.api.deps import get_db, get_embedder
from corebot_ai.backends.base import Embedder
from corebot_ai.config import settings
from corebot_ai.ingestion.pipeline import ingest_pipeline

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
) -> dict[str, str]:
    content = await file.read()
    try:
        doc_id = await ingest_pipeline(
            file.filename or "unknown",
            content,
            file.content_type or "text/plain",
            db,
            embedder,
        )
    except ResponseError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    f'Ollama embedding model "{settings.ollama_embed_model}" is missing. '
                    f'Run: ollama pull {settings.ollama_embed_model}'
                ),
            ) from exc
        raise HTTPException(status_code=503, detail=f"Ollama error: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Database/vector schema mismatch. Ensure EMBEDDING_DIM matches the model "
                "and recreate DB tables."
            ),
        ) from exc
    return {"document_id": str(doc_id)}
