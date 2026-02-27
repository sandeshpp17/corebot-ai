"""Pluggable diagnostics tool interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DiagnosticToolProvider(ABC):
    """Interface for webapp diagnostics providers."""

    @abstractmethod
    def fetch_diagnostics(self, context: dict) -> dict:
        """Return normalized diagnostics payload for incident analysis."""
        raise NotImplementedError


class NullDiagnosticToolProvider(DiagnosticToolProvider):
    """No-op diagnostics provider when tools are disabled."""

    def fetch_diagnostics(self, context: dict) -> dict:
        """Return empty diagnostics payload."""
        return {"status": "unavailable", "checks": []}
