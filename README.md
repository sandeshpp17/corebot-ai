# Corebot-AI

Production-grade, pluggable RAG chatbot with CLI + FastAPI.

## Quickstart

```bash
uv sync --dev
cp .env.example .env
uv run corebot --help
```

Set API key for CLI remote mode:

```bash
export COREBOT_API_KEY=corebot-dev-key
```

## Run

```bash
uv run corebot serve
```

For Ollama, ensure both chat and embedding models exist:

```bash
ollama pull phi3:mini
ollama pull nomic-embed-text
```

Recommended performance settings:

```bash
EMBEDDING_DIM=768
OLLAMA_TIMEOUT_SEC=120
OLLAMA_EMBED_CONCURRENCY=8
CHUNK_SIZE=600
CHUNK_OVERLAP=60
RETRIEVE_TOP_K=3
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SEC=300
```

## CLI

```bash
uv run corebot ingest README.md
uv run corebot ingest README.md --host http://localhost:8000
uv run corebot ingest README.md --host http://localhost:8000 --timeout 300
uv run corebot chat
uv run corebot chat --host http://localhost:8000
```

Chat controls:
- `exit` or `quit`: leave chat
- `/edit`: edit and resend previous user message
- `/undo`: remove last user+assistant turn
- `/history`: show number of turns
- `/help`: show commands

## API

- `POST /ingest/documents` (multipart file upload)
- `POST /ingest/documents/async` (background ingestion job)
- `GET /ingest/jobs/{job_id}` (ingestion job status)
- `POST /chat/` with JSON body: `{"message": "...", "history": []}`
- `GET /health`

All non-health endpoints require `X-API-Key`.

Chat test:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "X-API-Key: corebot-dev-key" \
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
- `${OLLAMA_EMBED_MODEL:-nomic-embed-text}`
only if it is not already installed.

By default, chat uses `phi3:mini` and embeddings use `nomic-embed-text` (768-dim).

If you change embedding dimension, recreate the database tables/volume.
