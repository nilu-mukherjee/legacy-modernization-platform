"""
CodeLens AI — Redis Client Setup.

Provides an async Redis client for caching and as the backing store for the
ARQ job queue.  The ``RedisClient`` wrapper exposes convenience helpers that
handle JSON serialisation and key expiry.

Usage in routes::

    @router.get("/cached")
    async def cached_endpoint(redis: RedisClient = Depends(get_redis)):
        cached = await redis.get("my_key")
        ...
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import settings

# ---------------------------------------------------------------------------
# Module-level connection pool (lazy — created on first ``get_redis()`` call).
# ---------------------------------------------------------------------------
_redis_pool: Redis | None = None


async def _get_pool() -> Redis:
    """Return the module-level Redis connection pool, creating it if needed.

    Returns:
        A ``redis.asyncio.Redis`` instance backed by a connection pool.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,  # Return ``str`` instead of ``bytes``
        )
    return _redis_pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Should be called during application shutdown.
    """
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


# ---------------------------------------------------------------------------
# Convenience Wrapper
# ---------------------------------------------------------------------------
class RedisClient:
    """Thin wrapper around ``redis.asyncio.Redis`` with JSON helpers.

    This class does **not** manage the connection itself — it receives an
    already-initialised ``Redis`` instance and adds domain-specific helpers.
    """

    def __init__(self, redis: Redis) -> None:
        """Initialise the client.

        Args:
            redis: An async Redis connection.
        """
        self._redis = redis

    # -- String commands (with automatic JSON serialisation) ----------------

    async def get(self, key: str) -> Any | None:
        """Retrieve a JSON-serialised value by key.

        Args:
            key: The Redis key.

        Returns:
            The deserialised Python object, or ``None`` if the key is absent.
        """
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> None:
        """Store a value as JSON under the given key.

        Args:
            key: The Redis key.
            value: Any JSON-serialisable Python object.
            expire: Optional TTL in seconds.
        """
        serialised = json.dumps(value, default=str)
        if expire:
            await self._redis.setex(key, expire, serialised)
        else:
            await self._redis.set(key, serialised)

    # -- Hash commands -----------------------------------------------------

    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        """Set multiple fields in a hash.

        Args:
            name: The hash key.
            mapping: Field-value pairs to store.
        """
        # Serialise each value to a JSON string so complex objects survive.
        serialised = {k: json.dumps(v, default=str) for k, v in mapping.items()}
        await self._redis.hset(name, mapping=serialised)

    async def hgetall(self, name: str) -> dict[str, Any]:
        """Retrieve all fields from a hash, deserialising JSON values.

        Args:
            name: The hash key.

        Returns:
            A dict of field → deserialised value.
        """
        raw = await self._redis.hgetall(name)
        result: dict[str, Any] = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    # -- Utility -----------------------------------------------------------

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys.

        Args:
            keys: Key name(s) to delete.

        Returns:
            The number of keys that were removed.
        """
        return await self._redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check whether a key exists.

        Args:
            key: The key to test.

        Returns:
            ``True`` if the key is present.
        """
        return bool(await self._redis.exists(key))


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------
async def get_redis() -> AsyncGenerator[RedisClient, None]:
    """FastAPI dependency that yields a :class:`RedisClient` per-request.

    Yields:
        A ``RedisClient`` backed by the shared connection pool.
    """
    pool = await _get_pool()
    yield RedisClient(pool)
