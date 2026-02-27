"""Intent detection helpers for assistant mode routing."""

from __future__ import annotations


INCIDENT_KEYWORDS = {
    "error",
    "fail",
    "failed",
    "issue",
    "incident",
    "down",
    "outage",
    "bug",
    "crash",
    "exception",
    "timeout",
    "not working",
}


def detect_mode(message: str, requested_mode: str | None = None) -> str:
    """Return effective mode: info or incident."""
    mode = (requested_mode or "auto").strip().lower()
    if mode in {"info", "incident"}:
        return mode

    lowered = message.lower()
    if any(keyword in lowered for keyword in INCIDENT_KEYWORDS):
        return "incident"
    return "info"
