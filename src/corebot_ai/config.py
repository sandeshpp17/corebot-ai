"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for API, database, and model settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "corebot-ai"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_key: str = ""
    cors_allow_origins: str = "http://localhost:3000"
    cors_allow_methods: str = "GET,POST,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,X-API-Key"
    cors_allow_credentials: bool = False

    database_url: str = Field(default="postgresql+psycopg2://corebot:corebot@localhost:5432/corebot")

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "phi3:mini"
    ollama_embed_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    ollama_timeout_sec: int = 120
    ollama_embed_concurrency: int = 8

    redis_url: str | None = "redis://localhost:6379/0"
    cache_ttl_sec: int = 300

    chunk_size: int = 600
    chunk_overlap: int = 60
    retrieve_top_k: int = 3
    retrieve_min_score: float = 0.6
    max_upload_bytes: int = 5 * 1024 * 1024
    max_history_messages: int = 20
    max_message_chars: int = 4000
    allowed_mime_types: str = "text/plain,text/markdown,application/json"
    max_ingest_jobs: int = 200
    ingest_job_ttl_sec: int = 3600

    webapp_tools_enabled: bool = False
    webapp_diagnostics_base_url: str = ""
    webapp_diagnostics_token: str = ""

    def parse_csv(self, value: str) -> list[str]:
        """Parse comma-separated setting values."""
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
