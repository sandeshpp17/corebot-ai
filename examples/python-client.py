"""Minimal Python client example for the chat endpoint."""

import requests


def chat(
    api_url: str,
    api_key: str,
    message: str,
    mode: str = "auto",
    history: list[dict] | None = None,
    app_context: dict | None = None,
) -> dict:
    """Send an authenticated chat request to Corebot API and return JSON response."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    resp = requests.post(
        f"{api_url}/chat/",
        json={
            "message": message,
            "history": history or [],
            "mode": mode,
            "app_context": app_context or {},
        },
        headers=headers,
        timeout=30,
    )
    if not resp.ok:
        try:
            detail = resp.json()
        except ValueError:
            detail = {"detail": resp.text}
        raise RuntimeError(f"Corebot request failed ({resp.status_code}): {detail}")
    return resp.json()
