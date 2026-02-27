# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy ALL project files for build + runtime
COPY pyproject.toml uv.lock* README.md src .env ./

# Install deps + project (editable-style, no wheel)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -e .

RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["corebot", "serve"]
