"""Ingestion API routes."""

from __future__ import annotations

import asyncio
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from ollama import ResponseError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from corebot_ai.api.deps import get_db, get_embedder, require_api_key
from corebot_ai.backends.base import Embedder
from corebot_ai.config import settings
from corebot_ai.database import SessionLocal
from corebot_ai.ingestion.pipeline import ingest_pipeline

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(require_api_key)])
ingest_jobs: dict[str, dict[str, str | float | None]] = {}
logger = logging.getLogger(__name__)


def _prune_jobs() -> None:
    """Bound job table by TTL and max records."""
    now = time.time()
    ttl = settings.ingest_job_ttl_sec
    expired = [
        job_id
        for job_id, item in ingest_jobs.items()
        if float(item.get("updated_at", now)) + ttl < now
    ]
    for job_id in expired:
        ingest_jobs.pop(job_id, None)
    while len(ingest_jobs) > settings.max_ingest_jobs:
        oldest_job = min(
            ingest_jobs.items(),
            key=lambda pair: float(pair[1].get("updated_at", now)),
        )[0]
        ingest_jobs.pop(oldest_job, None)


def _run_ingest_job(job_id: str, filename: str, content: bytes, mime_type: str) -> None:
    """Run ingestion in background and record job status."""
    db = SessionLocal()
    embedder = get_embedder()
    ingest_jobs[job_id] = {
        "status": "running",
        "document_id": None,
        "error": None,
        "updated_at": time.time(),
    }
    try:
        doc_id = asyncio.run(ingest_pipeline(filename, content, mime_type, db, embedder))
        ingest_jobs[job_id] = {
            "status": "completed",
            "document_id": str(doc_id),
            "error": None,
            "updated_at": time.time(),
        }
    except Exception as exc:
        logger.exception("Ingestion job %s failed: %s", job_id, exc)
        ingest_jobs[job_id] = {
            "status": "failed",
            "document_id": None,
            "error": "Ingestion failed.",
            "updated_at": time.time(),
        }
    finally:
        db.close()
        _prune_jobs()


async def _read_limited(upload: UploadFile) -> bytes:
    """Read upload payload with maximum size guard."""
    content = await upload.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max allowed is {settings.max_upload_bytes} bytes.",
        )
    return content


def _validate_mime(upload: UploadFile) -> None:
    """Validate file MIME type against allowlist."""
    allowed = set(settings.parse_csv(settings.allowed_mime_types))
    mime = (upload.content_type or "").lower()
    if mime not in allowed:
        raise HTTPException(status_code=415, detail=f"Unsupported MIME type: {upload.content_type}")


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
) -> dict[str, str]:
    """Ingest an uploaded document and return its id."""
    _validate_mime(file)
    content = await _read_limited(file)
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Database/vector schema mismatch. Ensure EMBEDDING_DIM matches the model "
                "and recreate DB tables."
            ),
        ) from exc
    return {"document_id": str(doc_id)}


@router.post("/documents/async")
async def upload_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Queue ingestion job and return a job identifier."""
    _prune_jobs()
    _validate_mime(file)
    content = await _read_limited(file)
    job_id = str(uuid4())
    ingest_jobs[job_id] = {
        "status": "queued",
        "document_id": None,
        "error": None,
        "updated_at": time.time(),
    }
    background_tasks.add_task(
        _run_ingest_job,
        job_id,
        file.filename or "unknown",
        content,
        file.content_type or "text/plain",
    )
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_ingest_job(job_id: str) -> dict[str, str | None]:
    """Return ingestion job status by id."""
    _prune_jobs()
    job = ingest_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "status": str(job.get("status")),
        "document_id": (str(job.get("document_id")) if job.get("document_id") else None),
        "error": (str(job.get("error")) if job.get("error") else None),
    }
