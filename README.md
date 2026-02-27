# Corebot-AI

Production-grade, pluggable RAG chatbot with CLI + FastAPI.

## Quickstart

```bash
uv sync --dev
cp .env.example .env
uv run corebot --help
```

## Run

```bash
uv run corebot serve
```

For Ollama, ensure both chat and embedding models exist:

```bash
ollama pull phi3:mini
```

Set embedding size for `phi3:mini`:

```bash
EMBEDDING_DIM=3072
OLLAMA_TIMEOUT_SEC=120
OLLAMA_EMBED_CONCURRENCY=4
```

## CLI

```bash
uv run corebot ingest README.md
uv run corebot ingest README.md --host http://localhost:8000
uv run corebot ingest README.md --host http://localhost:8000 --timeout 300
uv run corebot chat
uv run corebot chat --host http://localhost:8000
```

## API

- `POST /ingest/documents` (multipart file upload)
- `POST /chat/` with JSON body: `{"message": "...", "history": []}`
- `GET /health`

Chat test:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message":"what is corebotai","history":[]}'
```

## Architecture

- `corebot_ai/backends`: pluggable `Embedder` and `LLM` interfaces
- `corebot_ai/ingestion`: extraction + chunking + embedding + persistence
- `corebot_ai/retrieval`: semantic search with pgvector
- `corebot_ai/rag`: retrieve + prompt + generate pipeline
- `corebot_ai/api`: FastAPI app and routers
- `corebot_ai/cli.py`: `ingest`, `chat`, `serve`

## Docker

```bash
docker compose up --build
```

`docker compose` includes an `ollama-init` step that pulls:
- `${OLLAMA_CHAT_MODEL:-phi3:mini}`
only if it is not already installed.

By default, chat and embedding both use `phi3:mini`.

If you change model or embedding dimension, recreate the database tables/volume.
