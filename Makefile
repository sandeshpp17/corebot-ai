.PHONY: sync lint test serve up down

sync:
	uv sync --dev

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

test:
	uv run pytest -q

serve:
	uv run corebot serve

up:
	docker compose up --build

down:
	docker compose down -v
