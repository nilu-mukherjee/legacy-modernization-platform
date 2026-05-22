"""
Redis Client
=============

Async Redis client for job-queue operations, caching, and real-time progress
tracking.  Uses ``redis.asyncio`` under the hood.

Usage::

    from app.core.redis import get_redis, RedisClient

    @router.get("/job/{job_id}")
    async def job_status(job_id: str, r: RedisClient = Depends(get_redis)):
        return await r.hgetall(f"job:{job_id}")
"""

from __future__ import annotations

from typing import Any, Optional

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings

# ── Global connection pools ──────────────────────────────────────────────────
_pool: Optional[aioredis.Redis] = None
_arq_pool: Optional[ArqRedis] = None


async def init_redis() -> aioredis.Redis:
    """Create (or return existing) Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


class RedisClient:
    """
    Thin wrapper around ``redis.asyncio.Redis`` with convenience helpers.

    Injected into route handlers via :func:`get_redis`.
    """

    def __init__(self, conn: aioredis.Redis) -> None:
        self._r = conn

    async def get(self, key: str) -> Optional[str]:
        """Get a string value by key."""
        return await self._r.get(key)

    async def set(
        self, key: str, value: str, ex: Optional[int] = None
    ) -> None:
        """Set a string value with an optional TTL (seconds)."""
        await self._r.set(key, value, ex=ex)

    async def hset(self, key: str, mapping: dict[str, Any]) -> None:
        """Set multiple hash fields at once."""
        await self._r.hset(key, mapping=mapping)  # type: ignore[arg-type]

    async def hgetall(self, key: str) -> dict[str, str]:
        """Return all fields and values of a hash."""
        return await self._r.hgetall(key)  # type: ignore[return-value]

    async def delete(self, *keys: str) -> None:
        """Delete one or more keys."""
        await self._r.delete(*keys)

    async def ping(self) -> bool:
        """Health check — returns ``True`` if Redis is reachable."""
        return await self._r.ping()  # type: ignore[return-value]


async def get_redis() -> RedisClient:
    """FastAPI dependency that returns a :class:`RedisClient` instance."""
    conn = await init_redis()
    return RedisClient(conn)


async def init_arq() -> ArqRedis:
    """Create (or return existing) ARQ job-queue pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return _arq_pool


async def close_arq() -> None:
    """Close the ARQ pool."""
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None


async def get_arq_pool() -> ArqRedis:
    """FastAPI dependency that returns the ARQ job-queue pool."""
    return await init_arq()
