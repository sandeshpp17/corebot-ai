import requests


def chat(api_url: str, message: str) -> dict:
    resp = requests.post(f"{api_url}/chat/", json={"message": message, "history": []}, timeout=30)
    resp.raise_for_status()
    return resp.json()
