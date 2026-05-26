"""
Rate Limiting
=============

Redis-backed per-user rate limiting using fixed-window counters.

Usage::

    from app.core.rate_limit import check_rate_limit

    allowed, remaining, reset_in = await check_rate_limit(
        user_id=current_user.id,
        key="analysis",
        max_count=settings.MAX_ANALYSES_PER_USER_PER_DAY,
        window_seconds=86400,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Daily analysis limit reached")
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from app.core.redis import init_redis

logger = logging.getLogger(__name__)


async def check_rate_limit(
    user_id: UUID | str,
    key: str,
    max_count: int,
    window_seconds: int = 86400,
) -> tuple[bool, int, int]:
    """Increment the user's counter for ``key`` and check against the limit.

    Args:
        user_id: User UUID.
        key: Bucket name (e.g. ``"analysis"``).
        max_count: Maximum allowed within the window.
        window_seconds: Window length in seconds (default 24h).

    Returns:
        ``(allowed, remaining, ttl_seconds)``.
        ``allowed`` is False if the counter would exceed ``max_count``.
        ``remaining`` is the count left after this call (0 if blocked).
        ``ttl_seconds`` is when the window resets.
    """
    redis = await init_redis()
    bucket = _current_bucket(window_seconds)
    redis_key = f"ratelimit:{user_id}:{key}:{bucket}"

    try:
        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, window_seconds)
        ttl = await redis.ttl(redis_key)
        ttl = ttl if isinstance(ttl, int) and ttl > 0 else window_seconds

        if count > max_count:
            return False, 0, ttl
        return True, max(0, max_count - count), ttl
    except Exception as exc:  # noqa: BLE001
        # Fail open on Redis error so the app stays usable.
        logger.warning("rate_limit: redis error (failing open): %s", exc)
        return True, max_count, window_seconds


async def peek_rate_limit(
    user_id: UUID | str,
    key: str,
    max_count: int,
    window_seconds: int = 86400,
) -> tuple[int, int]:
    """Read current count + reset TTL without incrementing.

    Returns ``(remaining, ttl_seconds)``.
    """
    redis = await init_redis()
    bucket = _current_bucket(window_seconds)
    redis_key = f"ratelimit:{user_id}:{key}:{bucket}"
    try:
        raw = await redis.get(redis_key)
        count = int(raw) if raw else 0
        ttl = await redis.ttl(redis_key)
        ttl = ttl if isinstance(ttl, int) and ttl > 0 else window_seconds
        return max(0, max_count - count), ttl
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate_limit: redis error on peek: %s", exc)
        return max_count, window_seconds


def _current_bucket(window_seconds: int) -> str:
    """Compute a stable bucket identifier for the current window."""
    if window_seconds == 86400:
        return datetime.now(timezone.utc).strftime("%Y%m%d")
    epoch = int(datetime.now(timezone.utc).timestamp())
    return str(epoch - (epoch % window_seconds))
