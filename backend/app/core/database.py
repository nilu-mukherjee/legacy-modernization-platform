"""
Async Database Engine & Session Factory
========================================

Provides the SQLAlchemy 2.0 async engine, scoped session maker, and the
declarative ``Base`` class used by all ORM models.

Usage in FastAPI routes::

    from app.core.database import get_db

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ───────────────────────────────────────────────────────────────────
# ``pool_pre_ping`` drops stale connections before they cause errors.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ──────────────────────────────────────────────────────────
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy ORM models.

    Every model in ``app.models`` inherits from this class so that Alembic can
    auto-detect schema changes.
    """

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an ``AsyncSession``.

    The session is automatically closed when the request finishes, regardless
    of whether an exception occurred.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
