FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . /app

RUN uv venv && uv pip install -r requirements.txt

EXPOSE 5000

CMD ["/bin/bash","-c","uv run main.py"]
