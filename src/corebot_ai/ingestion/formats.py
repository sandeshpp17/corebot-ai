from __future__ import annotations


def _decode_bytes(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


async def extract_text(content: bytes, mime_type: str) -> str:
    handlers = {
        "text/markdown": _decode_bytes,
        "text/plain": _decode_bytes,
        "application/json": _decode_bytes,
    }
    return handlers.get(mime_type or "", _decode_bytes)(content)
