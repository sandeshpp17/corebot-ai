# Todo App + Corebot Integration

This Flask Todo app is integrated with Corebot through backend proxy endpoints.

## Prerequisites

- Corebot API is running (default: `http://localhost:8000`)
- Corebot `API_KEY` is set (example: `corebot-dev-key`)
- Python dependencies installed:

```bash
pip install -r requirements.txt
```

## Required environment variables (Flask app)

```bash
export COREBOT_URL=http://localhost:8000
export COREBOT_API_KEY=corebot-dev-key
export COREBOT_TIMEOUT_SEC=120
export APP_VERSION=todo-app-1.0.0
```

`COREBOT_API_KEY` is mandatory for this integration.

## Run

```bash
python main.py
```

App URL: `http://localhost:5000`

## Integrated routes

- `POST /assistant/chat`
  - Proxies to Corebot `POST /chat/`
  - Always sends `X-API-Key: COREBOT_API_KEY`
  - Payload:
    - `message` (required)
    - `history` (optional list)
    - `mode` (`auto|info|incident`)
    - `app_context` (optional object)

- `GET /support/context`
  - Diagnostics endpoint for Corebot incident mode tools.
  - Optional auth via `WEBAPP_DIAGNOSTICS_TOKEN`.

## Quick tests

Info mode:

```bash
curl -X POST http://localhost:5000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is this app?","mode":"info","history":[]}'
```

Incident mode:

```bash
curl -X POST http://localhost:5000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"todo delete failing","mode":"incident","history":[],"app_context":{"trace_id":"abc-123","session_id":"web-1"}}'
```

## Frontend integration

`templates/index.html` includes a built-in chat panel that calls `/assistant/chat`.

## Optional diagnostics token

To protect `/support/context`:

```bash
export WEBAPP_DIAGNOSTICS_TOKEN=your-token
```

Then set the same token in Corebot env:

```bash
WEBAPP_TOOLS_ENABLED=true
WEBAPP_DIAGNOSTICS_BASE_URL=http://host.docker.internal:5000
WEBAPP_DIAGNOSTICS_TOKEN=your-token
```
