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
- `POST /chat/` with JSON body:
  `{"message":"...","history":[],"mode":"auto|info|incident","app_context":{...}}`
- `GET /health`

Integration requirement: set `API_KEY` and send `X-API-Key` on all non-health endpoints.

Chat test:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "X-API-Key: corebot-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"message":"what is corebotai","history":[],"mode":"info"}'
```

Incident-mode example for webapp integration:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "X-API-Key: corebot-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"message":"Checkout keeps failing with 500","mode":"incident","history":[],"app_context":{"trace_id":"abc-123","session_id":"s-42","app_version":"1.9.2"}}'
```

## Architecture

- `corebot_ai/backends`: pluggable `Embedder` and `LLM` interfaces
- `corebot_ai/ingestion`: extraction + chunking + embedding + persistence
- `corebot_ai/retrieval`: semantic search with pgvector
- `corebot_ai/rag`: retrieve + prompt + generate pipeline
- `corebot_ai/assistant`: auto-routing between info and incident assistance
- `corebot_ai/tools`: pluggable diagnostics providers for webapp integrations
- `corebot_ai/api`: FastAPI app and routers
- `corebot_ai/cli.py`: `ingest`, `chat`, `serve`

Webapp diagnostics tool settings:
- `WEBAPP_TOOLS_ENABLED=true`
- `WEBAPP_DIAGNOSTICS_BASE_URL=https://your-webapp-api`
- `WEBAPP_DIAGNOSTICS_TOKEN=...`

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
