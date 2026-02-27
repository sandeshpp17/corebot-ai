"""Minimal Python client example for the chat endpoint."""

import requests


def chat(api_url: str, message: str) -> dict:
    """Send a chat request to Corebot API and return JSON response."""
    resp = requests.post(f"{api_url}/chat/", json={"message": message, "history": []}, timeout=30)
    resp.raise_for_status()
    return resp.json()
