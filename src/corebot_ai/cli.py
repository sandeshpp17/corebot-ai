from __future__ import annotations

import asyncio
import json
import mimetypes
from pathlib import Path
from urllib import error, request

import click
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
    boundary = "----corebot-boundary"
    content = file.read_bytes()
    mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def _ingest_remote(host: str, file: Path) -> str:
    body, boundary = _build_multipart(file)
    url = f"{host.rstrip('/')}/ingest/documents"
    req = request.Request(
        url=url,
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return str(payload.get("document_id", "unknown"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise click.ClickException(f"Remote ingest failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise click.ClickException(f"Could not reach Corebot API at {url}: {exc}") from exc


def _chat_remote(host: str, message: str, history: list[dict]) -> dict:
    url = f"{host.rstrip('/')}/chat/"
    payload = json.dumps({"message": message, "history": history}).encode("utf-8")
    req = request.Request(
        url=url,
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise click.ClickException(f"Remote chat failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise click.ClickException(f"Could not reach Corebot API at {url}: {exc}") from exc


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--host", type=str, default=None, help="Corebot API base URL, e.g. http://localhost:8000")
def ingest(file: Path, host: str | None) -> None:
    """Ingest a document file."""
    if host:
        doc_id = _ingest_remote(host, file)
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
def chat(host: str | None) -> None:
    """Run an interactive RAG chat session."""
    history: list[dict] = []

    if host:
        console.print(f"Remote chat mode: [cyan]{host}[/cyan]. Type `exit` to quit.")
        while True:
            message = click.prompt("You")
            if message.lower().strip() in {"exit", "quit"}:
                break

            result = _chat_remote(host, message, history)
            history.extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": result["reply"]},
                ]
            )

            console.print(f"[bold green]Bot:[/bold green] {result['reply']}")
            if result.get("sources"):
                table = Table(title="Sources")
                table.add_column("Source")
                table.add_column("Score")
                for src in result["sources"]:
                    table.add_row(str(src["source"]), f"{float(src['score']):.3f}")
                console.print(table)
        return

    init_db()
    db = SessionLocal()
    try:
        console.print("Local chat mode. Type `exit` to quit.")
        while True:
            message = click.prompt("You")
            if message.lower().strip() in {"exit", "quit"}:
                break

            result = asyncio.run(rag_chat(message, history, get_embedder(), get_llm(), db))
            history.extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": result["reply"]},
                ]
            )

            console.print(f"[bold green]Bot:[/bold green] {result['reply']}")
            if result["sources"]:
                table = Table(title="Sources")
                table.add_column("Source")
                table.add_column("Score")
                for src in result["sources"]:
                    table.add_row(str(src["source"]), f"{float(src['score']):.3f}")
                console.print(table)
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
