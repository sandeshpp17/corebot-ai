"""HTTP diagnostics provider for integrated web applications."""

from __future__ import annotations

import json
from urllib import error, parse, request

from corebot_ai.tools.base import DiagnosticToolProvider


class WebAppDiagnosticToolProvider(DiagnosticToolProvider):
    """Fetch diagnostics from a webapp support endpoint."""

    def __init__(self, base_url: str, token: str) -> None:
        """Initialize with base diagnostics URL and bearer token."""
        self.base_url = base_url.rstrip("/")
        self.token = token

    def fetch_diagnostics(self, context: dict) -> dict:
        """Call webapp diagnostics endpoint and return JSON payload."""
        query = parse.urlencode({k: str(v) for k, v in context.items() if v is not None})
        url = f"{self.base_url}/support/context"
        if query:
            url = f"{url}?{query}"

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = request.Request(url=url, method="GET", headers=headers)
        try:
            with request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (error.URLError, error.HTTPError, json.JSONDecodeError) as exc:
            return {
                "status": "error",
                "checks": [],
                "error": f"Diagnostics unavailable: {exc}",
            }
