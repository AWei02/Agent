"""Async SQLAlchemy database infrastructure used by FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# Never replace this with a synchronous engine in request handlers.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields one transaction-capable async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
