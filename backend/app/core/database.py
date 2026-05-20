"""
CodeLens AI — Async Database Setup.

Creates the async SQLAlchemy engine, session factory, and the declarative
``Base`` class used by all ORM models.  Also exposes the ``get_db()``
dependency for FastAPI route injection.

Usage in routes::

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — one per process, manages the connection pool.
# ---------------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,          # Log SQL statements in dev
    pool_size=10,                     # Maximum number of persistent connections
    max_overflow=20,                  # Extra connections allowed beyond pool_size
    pool_pre_ping=True,               # Verify connections before use
    pool_recycle=300,                 # Recycle connections every 5 minutes
)

# ---------------------------------------------------------------------------
# Session factory — produces ``AsyncSession`` instances.
# ---------------------------------------------------------------------------
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,           # Keep attributes accessible after commit
)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Subclass this to define database tables.  The ``metadata`` attribute is
    shared across all models and used by Alembic for migrations.
    """

    pass


# ---------------------------------------------------------------------------
# Dependency — yields an async session per-request.
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session.

    Opens a session, yields it to the route handler, and automatically
    closes it when the request completes (even on error).

    Yields:
        An ``AsyncSession`` bound to the application's engine.
    """
    async with async_session_maker() as session:
        try:
            yield session
            # Commit any pending changes made by the route handler.
            await session.commit()
        except Exception:
            # Roll back on any unhandled exception to leave the DB clean.
            await session.rollback()
            raise
        finally:
            await session.close()
