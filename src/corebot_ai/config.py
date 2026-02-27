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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
