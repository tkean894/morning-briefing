from sqlalchemy import create_engine

from app.config import settings


def _normalize_url(url: str) -> str:
    """Ensure the psycopg3 driver is used regardless of how the URL was supplied
    (Neon and most providers hand out plain postgresql:// / postgres:// URLs)."""
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(_normalize_url(settings.database_url), pool_pre_ping=True)
