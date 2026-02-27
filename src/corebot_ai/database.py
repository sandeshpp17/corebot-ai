"""Database engine, session management, and initialization helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from corebot_ai.config import settings
from corebot_ai.models import Base


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Ensure required extensions exist and create tables."""
    with engine.begin() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Failed to enable pgvector extension. "
                "Use a Postgres instance with pgvector installed "
                "(for Docker, use image `pgvector/pgvector:pg16`)."
            ) from exc
    Base.metadata.create_all(bind=engine)
