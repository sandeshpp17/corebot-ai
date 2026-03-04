# Corebot-AI

Production-grade, pluggable RAG chatbot with CLI + FastAPI.

## Prerequisites

Install these first:

- Docker + Docker Compose (official): https://docs.docker.com/engine/install/
- `uv` package manager (official): https://docs.astral.sh/uv/getting-started/installation/

Optional but useful for local model checks:

- Ollama CLI: https://ollama.com/download

## Quick Start

### Option A: Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Corebot API will be available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

### Option B: Local development with `uv`

```bash
uv sync --dev
cp .env.example .env
uv run corebot serve
```

## Deploy Corebot

For server/container deployment:

1. Set production env vars in `.env`:

```bash
API_KEY=<strong-secret>
CORS_ALLOW_ORIGINS=https://your-webapp-domain
```

2. Start stack:

```bash
docker compose up -d --build
```

3. Validate deployment:

```bash
curl http://localhost:8000/health
```

4. Ingest documents:

```bash
curl -X POST "http://localhost:8000/ingest/documents" \
  -H "X-API-Key: <strong-secret>" \
  -F "file=@README.md"
```

## Security for Integration

Integration requirement: set `API_KEY` and send `X-API-Key` on all non-health endpoints.

Example:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "X-API-Key: corebot-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"message":"what is corebotai","history":[],"mode":"info"}'
```

## API

- `POST /ingest/documents` (multipart file upload)
- `POST /ingest/documents/async` (background ingestion job)
- `GET /ingest/jobs/{job_id}` (ingestion job status)
- `POST /chat/` body:
  `{"message":"...","history":[],"mode":"auto|info|incident","app_context":{...}}`
- `GET /health`

Incident-mode example:

```bash
curl -i -X POST "http://localhost:8000/chat/" \
  -H "X-API-Key: corebot-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"message":"Checkout failing with 500","mode":"incident","history":[],"app_context":{"trace_id":"abc-123","session_id":"s-42","app_version":"1.9.2"}}'
```

## CLI

```bash
uv run corebot ingest README.md
uv run corebot ingest README.md --host http://localhost:8000 --timeout 300 --api-key corebot-dev-key
uv run corebot chat
uv run corebot chat --host http://localhost:8000 --api-key corebot-dev-key
```

Chat controls:

- `exit` or `quit`
- `/edit`
- `/undo`
- `/history`
- `/help`

## Performance Defaults

Recommended defaults in `.env`:

```bash
OLLAMA_CHAT_MODEL=phi3:mini
OLLAMA_EMBED_MODEL=nomic-embed-text
EMBEDDING_DIM=768
OLLAMA_TIMEOUT_SEC=120
OLLAMA_EMBED_CONCURRENCY=8
CHUNK_SIZE=600
CHUNK_OVERLAP=60
RETRIEVE_TOP_K=3
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SEC=300
```

## Architecture

- `corebot_ai/backends`: pluggable `Embedder` and `LLM`
- `corebot_ai/ingestion`: extraction + chunking + embedding + persistence
- `corebot_ai/retrieval`: semantic search with pgvector
- `corebot_ai/rag`: retrieve + prompt + generate
- `corebot_ai/assistant`: auto routing (`info` / `incident`)
- `corebot_ai/tools`: pluggable diagnostics providers
- `corebot_ai/api`: FastAPI app + routers
- `corebot_ai/cli.py`: `ingest`, `chat`, `serve`

Webapp diagnostics settings:

- `WEBAPP_TOOLS_ENABLED=true`
- `WEBAPP_DIAGNOSTICS_BASE_URL=https://your-webapp-api`
- `WEBAPP_DIAGNOSTICS_TOKEN=...`

## Troubleshooting

1. `401 Invalid API key`
- Ensure `API_KEY` in Corebot `.env` matches the `X-API-Key` header sent by client.
- For CLI remote mode, use `--api-key` or export `COREBOT_API_KEY`.

2. `500 Database/vector schema mismatch`
- Happens when `EMBEDDING_DIM` or embedding model changed after tables were created.
- Recreate DB tables/volume and re-ingest:

```bash
docker compose down -v
docker compose up --build
```

3. `504 Chat request timed out while waiting for Ollama`
- Increase `OLLAMA_TIMEOUT_SEC` (for example `300` or `600`).
- Reduce `RETRIEVE_TOP_K`, `CHUNK_SIZE`, and `CHUNK_OVERLAP` to shrink prompt/retrieval cost.

4. Ingest fails with model errors (`model not found`)
- Pull required models:

```bash
ollama pull phi3:mini
ollama pull nomic-embed-text
```

5. Browser error: `Unexpected token '<'` in todo app chat
- Means backend returned HTML error instead of JSON.
- Check Flask logs and ensure `COREBOT_URL` and `COREBOT_API_KEY` are set correctly in todo app environment.

6. Async ingest job not found
- Job states are in-memory with TTL; old IDs expire.
- Retry ingestion and track fresh `job_id`.
