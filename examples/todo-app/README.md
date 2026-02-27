# Todo App + Corebot Integration

This Flask todo app includes a backend proxy to Corebot and a web chat panel.

## Prerequisites

- Corebot API must be running and reachable.
- Corebot `API_KEY` must be set (for example: `corebot-dev-key`).
- Python dependencies for this app installed:

```bash
pip install -r requirements.txt
```

## Required env vars (Flask app)

Set these before running the Flask app:

```bash
export COREBOT_URL=http://localhost:8000
export COREBOT_API_KEY=corebot-dev-key
export COREBOT_TIMEOUT_SEC=120
export APP_VERSION=todo-app-1.0.0
```

`COREBOT_API_KEY` is mandatory for integration.

## Run

```bash
python main.py
```

App runs on `http://localhost:5000`.

## Integrated endpoints

- `POST /assistant/chat`
  - Proxies requests to `POST $COREBOT_URL/chat/`
  - Sends `X-API-Key: $COREBOT_API_KEY`
  - Supports payload:
    - `message`
    - `history`
    - `mode` (`auto|info|incident`)
    - `app_context`

- `GET /support/context`
  - Diagnostics endpoint for Corebot incident mode tools
  - Optional bearer token check via `WEBAPP_DIAGNOSTICS_TOKEN`

## Quick tests

```bash
curl -X POST http://localhost:5000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"todo delete failing","mode":"incident","history":[],"app_context":{"trace_id":"abc-123","session_id":"web-1"}}'
```

```bash
curl -X POST http://localhost:5000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is this app?","mode":"info","history":[]}'
```

## Frontend

`templates/index.html` includes a built-in Corebot panel that calls `/assistant/chat` directly.

## Optional diagnostics auth

If you want to protect `/support/context`, set:

```bash
export WEBAPP_DIAGNOSTICS_TOKEN=your-token
```

Corebot should use the same token in its env:

```bash
WEBAPP_TOOLS_ENABLED=true
WEBAPP_DIAGNOSTICS_BASE_URL=http://host.docker.internal:5000
WEBAPP_DIAGNOSTICS_TOKEN=your-token
```
