"""Assistant pipeline with info/incident routing."""

from __future__ import annotations

from sqlalchemy.orm import Session

from corebot_ai.assistant.intent import detect_mode
from corebot_ai.backends.base import Embedder, LLM
from corebot_ai.rag.pipeline import rag_chat
from corebot_ai.tools.base import DiagnosticToolProvider


def _build_incident_prompt(message: str, history: list[dict], diagnostics: dict) -> str:
    """Build structured troubleshooting prompt for incident mode."""
    recent_history = "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history[-5:]
    )
    return (
        "You are Corebot incident assistant.\n"
        "1) Identify likely root cause\n"
        "2) Provide step-by-step checks\n"
        "3) Provide safe remediation options\n"
        "4) Provide escalation criteria\n\n"
        f"Conversation:\n{recent_history}\n\n"
        f"Diagnostics:\n{diagnostics}\n\n"
        f"User issue:\n{message}"
    )


async def assistant_chat(
    message: str,
    history: list[dict],
    mode: str | None,
    app_context: dict,
    embedder: Embedder,
    llm: LLM,
    db: Session,
    diagnostic_provider: DiagnosticToolProvider,
) -> dict:
    """Route requests to info or incident assistant flows."""
    effective_mode = detect_mode(message, mode)

    if effective_mode == "info":
        result = await rag_chat(message, history, embedder, llm, db)
        result["mode"] = "info"
        result["actions"] = []
        return result

    diagnostics = diagnostic_provider.fetch_diagnostics(app_context)
    system_prompt = _build_incident_prompt(message, history, diagnostics)
    response_text = await llm.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
    )

    actions: list[str] = []
    if diagnostics.get("status") == "error":
        actions.append("Collect trace_id/session_id and verify diagnostics endpoint availability.")
    else:
        actions.append("Follow the ordered checks in the response and validate after each step.")

    return {
        "reply": response_text,
        "sources": [],
        "context_used": 0,
        "mode": "incident",
        "actions": actions,
        "diagnostics_status": diagnostics.get("status", "unknown"),
    }
