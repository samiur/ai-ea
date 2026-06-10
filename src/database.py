# ABOUTME: Async database engine, session management, and connection health
# ABOUTME: Engine is lazily built from settings; tests can repoint it via configure_database

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession as SQLAlchemyAsyncSession,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import get_settings

_engine: AsyncEngine | None = None


def _async_url(url: str) -> str:
    """Map sync-style URLs from settings onto async drivers."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


def create_engine_for_url(url: str) -> AsyncEngine:
    """Build an async engine with the project's pool settings."""
    from sqlalchemy.ext.asyncio import create_async_engine

    url = _async_url(url)
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        # In-memory SQLite must share one connection across sessions
        kwargs = {"poolclass": StaticPool}
    else:
        kwargs |= {"pool_size": 5, "max_overflow": 10}
    return create_async_engine(url, **kwargs)


def get_engine() -> AsyncEngine:
    """Get the process-wide engine, building it from settings on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine_for_url(get_settings().database_url)
    return _engine


async def configure_database(url: str | None) -> None:
    """Repoint the database layer (tests); None restores the settings URL."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
    _engine = create_engine_for_url(url) if url else None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an async session with auto-rollback."""
    session = AsyncSession(get_engine(), expire_on_commit=False)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Create tables for all imported models (dev convenience; Alembic owns prod)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def check_database_connection() -> bool:
    """Check that the database accepts queries."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


async def dispose_engine() -> None:
    """Release pooled connections (app shutdown)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


__all__ = [
    "AsyncSession",
    "SQLAlchemyAsyncSession",
    "check_database_connection",
    "configure_database",
    "create_engine_for_url",
    "dispose_engine",
    "get_engine",
    "get_session",
    "init_db",
]
