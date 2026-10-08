"""Milestone 2 Database Infrastructure Tests."""

# pyrefly: ignore [missing-import]
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base, TimestampMixin
from app.core.database import get_db


@pytest.mark.asyncio
async def test_base_and_timestamp_mixin():
    """Verify DeclarativeBase and TimestampMixin definition."""
    assert Base is not None
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")


@pytest.mark.asyncio
async def test_get_db_session_lifecycle():
    """Verify that get_db yields an AsyncSession and closes cleanly."""
    generator = get_db()
    session = await anext(generator)
    assert isinstance(session, AsyncSession)

    # Cleanly finish the generator
    with pytest.raises(StopAsyncIteration):
        await anext(generator)


@pytest.mark.asyncio
async def test_async_engine_execution():
    """Verify asynchronous query execution with SQLite in-memory engine."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_sessionmaker() as session:
        result = await session.execute(text("SELECT 1 AS alive"))
        row = result.scalar_one()
        assert row == 1

    await test_engine.dispose()
