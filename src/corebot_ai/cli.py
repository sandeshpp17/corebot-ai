"""Command-line interface for local and remote Corebot operations."""

from __future__ import annotations

import asyncio
import json
import mimetypes
import socket
from pathlib import Path
from urllib import error, request

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from sqlalchemy.orm import Session
import uvicorn
from rich.console import Console
from rich.table import Table

from corebot_ai.api.deps import get_embedder, get_llm
from corebot_ai.config import settings
from corebot_ai.database import SessionLocal, init_db
from corebot_ai.ingestion.pipeline import ingest_pipeline
from corebot_ai.rag.pipeline import rag_chat

console = Console()


@click.group()
def main() -> None:
    """Corebot CLI."""


def _build_multipart(file: Path) -> tuple[bytes, str]:
    """Build multipart/form-data payload for file uploads."""
    boundary = "----corebot-boundary"
    content = file.read_bytes()
    mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def _ingest_remote(host: str, file: Path, timeout: int, api_key: str) -> str:
    """Upload a file to a remote Corebot ingest endpoint."""
    body, boundary = _build_multipart(file)
    url = f"{host.rstrip('/')}/ingest/documents"
    req = request.Request(
        url=url,
        method="POST",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-API-Key": api_key,
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return str(payload.get("document_id", "unknown"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise click.ClickException(f"Remote ingest failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise click.ClickException(f"Could not reach Corebot API at {url}: {exc}") from exc
    except TimeoutError as exc:
        raise click.ClickException(
            f"Remote ingest timed out after {timeout}s. Use --timeout to increase."
        ) from exc
    except socket.timeout as exc:
        raise click.ClickException(
            f"Remote ingest timed out after {timeout}s. Use --timeout to increase."
        ) from exc


def _chat_remote(host: str, message: str, history: list[dict], timeout: int, api_key: str) -> dict:
    """Send a chat request to a remote Corebot API."""
    url = f"{host.rstrip('/')}/chat/"
    payload = json.dumps({"message": message, "history": history}).encode("utf-8")
    req = request.Request(
        url=url,
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise click.ClickException(f"Remote chat failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise click.ClickException(f"Could not reach Corebot API at {url}: {exc}") from exc
    except TimeoutError as exc:
        raise click.ClickException(
            f"Remote chat timed out after {timeout}s. Use --timeout to increase."
        ) from exc
    except socket.timeout as exc:
        raise click.ClickException(
            f"Remote chat timed out after {timeout}s. Use --timeout to increase."
        ) from exc


def _show_sources(result: dict) -> None:
    """Render source table for a chat result."""
    sources = result.get("sources") or []
    if not sources:
        return
    table = Table(title="Sources")
    table.add_column("Source")
    table.add_column("Score")
    for src in sources:
        table.add_row(str(src["source"]), f"{float(src['score']):.3f}")
    console.print(table)


def _pop_last_turn(history: list[dict]) -> str | None:
    """Remove and return the last user message if a full turn exists."""
    if len(history) < 2:
        return None
    if history[-2].get("role") != "user" or history[-1].get("role") != "assistant":
        return None
    last_user_message = str(history[-2].get("content", ""))
    del history[-2:]
    return last_user_message


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--host", type=str, default=None, help="Corebot API base URL, e.g. http://localhost:8000")
@click.option("--timeout", type=int, default=300, show_default=True, help="HTTP timeout in seconds.")
@click.option(
    "--api-key",
    envvar="COREBOT_API_KEY",
    default=settings.api_key,
    show_default=False,
    help="API key for remote endpoints (or set COREBOT_API_KEY).",
)
def ingest(file: Path, host: str | None, timeout: int, api_key: str) -> None:
    """Ingest a document file."""
    if host:
        doc_id = _ingest_remote(host, file, timeout, api_key)
        console.print(
            f"Ingested [bold]{file}[/bold] via [cyan]{host}[/cyan] as document [green]{doc_id}[/green]"
        )
        return

    init_db()
    db = SessionLocal()
    try:
        content = file.read_bytes()
        mime_type = "text/markdown" if file.suffix.lower() in {".md", ".markdown"} else "text/plain"
        doc_id = asyncio.run(ingest_pipeline(file.name, content, mime_type, db, get_embedder()))
        console.print(f"Ingested [bold]{file}[/bold] as document [green]{doc_id}[/green]")
    finally:
        db.close()


@main.command()
@click.option("--host", type=str, default=None, help="Corebot API base URL, e.g. http://localhost:8000")
@click.option("--timeout", type=int, default=120, show_default=True, help="HTTP timeout in seconds.")
@click.option(
    "--api-key",
    envvar="COREBOT_API_KEY",
    default=settings.api_key,
    show_default=False,
    help="API key for remote endpoints (or set COREBOT_API_KEY).",
)
def chat(host: str | None, timeout: int, api_key: str) -> None:
    """Run an interactive RAG chat session."""
    history: list[dict] = []
    prompt_session = PromptSession(history=InMemoryHistory(), auto_suggest=AutoSuggestFromHistory())

    def _send(message: str, db: Session | None = None) -> dict:
        if host:
            return _chat_remote(host, message, history, timeout, api_key)
        assert db is not None
        return asyncio.run(rag_chat(message, history, get_embedder(), get_llm(), db))

    def _process_message(message: str, db: Session | None = None) -> None:
        result = _send(message, db)
        history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result["reply"]},
            ]
        )
        console.print(f"[bold green]Bot:[/bold green] {result['reply']}")
        _show_sources(result)

    if host:
        console.print(
            "Remote chat mode: "
            f"[cyan]{host}[/cyan]. Commands: /help, /undo, /edit, /history, exit"
        )
        while True:
            message = prompt_session.prompt("You: ").strip()
            if not message:
                continue
            if message.lower() in {"exit", "quit"}:
                break
            if message == "/help":
                console.print("Commands: /help, /undo, /edit, /history, exit")
                continue
            if message == "/history":
                turns = sum(1 for m in history if m.get("role") == "user")
                console.print(f"Turns: {turns}")
                continue
            if message == "/undo":
                removed = _pop_last_turn(history)
                if removed is None:
                    console.print("No complete turn to undo.")
                else:
                    console.print("Removed last turn.")
                continue
            if message == "/edit":
                last = _pop_last_turn(history)
                if last is None:
                    console.print("No previous turn to edit.")
                    continue
                edited = prompt_session.prompt("Edit last message: ", default=last).strip()
                if not edited:
                    console.print("Edit cancelled.")
                    continue
                _process_message(edited)
                continue
            _process_message(message)
        return

    init_db()
    db = SessionLocal()
    try:
        console.print("Local chat mode. Commands: /help, /undo, /edit, /history, exit")
        while True:
            message = prompt_session.prompt("You: ").strip()
            if not message:
                continue
            if message.lower() in {"exit", "quit"}:
                break
            if message == "/help":
                console.print("Commands: /help, /undo, /edit, /history, exit")
                continue
            if message == "/history":
                turns = sum(1 for m in history if m.get("role") == "user")
                console.print(f"Turns: {turns}")
                continue
            if message == "/undo":
                removed = _pop_last_turn(history)
                if removed is None:
                    console.print("No complete turn to undo.")
                else:
                    console.print("Removed last turn.")
                continue
            if message == "/edit":
                last = _pop_last_turn(history)
                if last is None:
                    console.print("No previous turn to edit.")
                    continue
                edited = prompt_session.prompt("Edit last message: ", default=last).strip()
                if not edited:
                    console.print("Edit cancelled.")
                    continue
                _process_message(edited, db)
                continue
            _process_message(message, db)
    finally:
        db.close()


@main.command()
def serve() -> None:
    """Start FastAPI server."""
    uvicorn.run(
        "corebot_ai.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
