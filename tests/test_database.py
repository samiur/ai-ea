# ABOUTME: Tests for SQLModel database setup and connection management (Step 11)
# ABOUTME: Session logic is tested against in-memory SQLite; live checks run when postgres is up

import os
import socket
from collections.abc import AsyncIterator
from urllib.parse import urlparse
from uuid import UUID

import pytest
from sqlmodel import Field, SQLModel, select

from src.database import (
    check_database_connection,
    configure_database,
    create_engine_for_url,
    get_engine,
    get_session,
)
from src.models.base import TimestampedModel

SQLITE_URL = "sqlite+aiosqlite:///:memory:"


def _postgres_reachable() -> bool:
    parsed = urlparse(os.environ.get("DATABASE_URL", ""))
    try:
        with socket.create_connection(
            (parsed.hostname or "localhost", parsed.port or 5432), timeout=2
        ):
            return True
    except OSError:
        return False


class _Note(TimestampedModel, table=True):
    """Throwaway model for exercising the session layer."""

    __tablename__ = "test_notes"
    text: str = Field(default="")


@pytest.fixture
async def sqlite_db() -> AsyncIterator[None]:
    """Point the database layer at a fresh in-memory SQLite DB."""
    await configure_database(SQLITE_URL)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await configure_database(None)  # restore settings-based engine


async def test_session_round_trip(sqlite_db: None) -> None:
    """Test create/commit/select through the session dependency."""
    async for session in get_session():
        note = _Note(text="hello")
        session.add(note)
        await session.commit()
        await session.refresh(note)

        assert isinstance(note.id, UUID)
        assert note.created_at is not None
        assert note.updated_at is not None

        result = await session.exec(select(_Note))
        notes = result.all()
        assert len(notes) == 1
        assert notes[0].text == "hello"


async def test_sessions_are_independent(sqlite_db: None) -> None:
    """Test that the dependency yields a usable, independent session per call."""
    async for first in get_session():
        first.add(_Note(text="one"))
        await first.commit()

    async for second in get_session():
        result = await second.exec(select(_Note))
        assert len(result.all()) == 1


async def test_check_database_connection_up(sqlite_db: None) -> None:
    """Test the connection check against a live (sqlite) database."""
    assert await check_database_connection() is True


async def test_check_database_connection_down() -> None:
    """Test the connection check against an unreachable database."""
    await configure_database("postgresql+asyncpg://nobody:nope@127.0.0.1:59999/nope")
    try:
        assert await check_database_connection() is False
    finally:
        await configure_database(None)


def test_postgres_engine_pool_configuration() -> None:
    """Test pool settings without connecting (engine creation is lazy)."""
    engine = create_engine_for_url("postgresql+asyncpg://u:p@localhost:5432/db")
    assert engine.pool.size() == 5
    assert engine.pool._max_overflow == 10  # type: ignore[attr-defined]


def test_async_url_conversion() -> None:
    """Test that sync-style URLs from settings get async drivers."""
    engine = create_engine_for_url("postgresql://u:p@localhost:5432/db")
    assert engine.url.drivername == "postgresql+asyncpg"


@pytest.mark.skipif(not _postgres_reachable(), reason="postgres not reachable")
async def test_live_postgres_connection() -> None:
    """Test a real round-trip against the provisioned postgres (CI service)."""
    await configure_database(None)
    assert await check_database_connection() is True
