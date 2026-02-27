"""File-format text extraction helpers."""

from __future__ import annotations

from corebot_ai.config import settings


def _decode_bytes(content: bytes) -> str:
    """Decode UTF-8 content while ignoring invalid bytes."""
    return content.decode("utf-8", errors="ignore")


async def extract_text(content: bytes, mime_type: str) -> str:
    """Extract plain text from supported MIME types."""
    handlers = {
        "text/markdown": _decode_bytes,
        "text/plain": _decode_bytes,
        "application/json": _decode_bytes,
    }
    normalized_mime = (mime_type or "").strip().lower()
    if normalized_mime not in settings.parse_csv(settings.allowed_mime_types):
        raise ValueError(f"Unsupported MIME type: {mime_type}")
    return handlers[normalized_mime](content)
