"""
Security Utilities
==================

Handles JWT token creation / verification, GitHub-token encryption, and the
``get_current_user`` dependency used to protect API routes.

Token Flow
----------
1. Frontend authenticates via GitHub OAuth (Auth.js v5).
2. Frontend calls ``POST /api/v1/auth/sync`` with the GitHub profile + token.
3. Backend upserts the user, encrypts the GitHub token, and returns a JWT.
4. Frontend sends the JWT on every subsequent request as
   ``Authorization: Bearer <jwt>``.
5. ``get_current_user()`` verifies the JWT and resolves the ``User`` object.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

# ── Constants ────────────────────────────────────────────────────────────────
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = 30

_bearer_scheme = HTTPBearer(auto_error=False)


# ── Token Encryption (Fernet / AES-128-CBC) ─────────────────────────────────


class TokenEncryptor:
    """
    Encrypt / decrypt sensitive strings (e.g. GitHub access tokens) using
    Fernet symmetric encryption.

    Args:
        key: A URL-safe base64-encoded 32-byte key. Generate one with::

            python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """

    def __init__(self, key: str) -> None:
        self._cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        """Return the Fernet-encrypted ciphertext (URL-safe base64)."""
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Return the original plaintext from a Fernet ciphertext."""
        return self._cipher.decrypt(ciphertext.encode()).decode()


def get_encryptor() -> TokenEncryptor:
    """Factory — returns a :class:`TokenEncryptor` with the app-wide key."""
    if not settings.ENCRYPTION_KEY:
        # Fallback for dev — NOT safe for production
        return TokenEncryptor(Fernet.generate_key().decode())
    return TokenEncryptor(settings.ENCRYPTION_KEY)


# ── JWT Helpers ──────────────────────────────────────────────────────────────


def create_access_token(
    user_id: str | UUID,
    *,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT containing the ``user_id`` as the ``sub`` claim.

    Args:
        user_id: UUID of the authenticated user.
        expires_delta: Custom expiration. Defaults to 30 days.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm=_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT and return the ``sub`` (user_id) claim.

    Returns:
        The user-id string, or ``None`` if the token is invalid / expired.
    """
    try:
        payload = jwt.decode(
            token, settings.AUTH_SECRET, algorithms=[_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


# ── FastAPI Dependency ───────────────────────────────────────────────────────


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        _bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency that extracts and validates the JWT from the
    ``Authorization`` header, then loads the corresponding ``User`` model.

    Raises:
        HTTPException 401: if the token is missing, invalid, or the user
            cannot be found.
    """
    # Import here to avoid circular dependency at module level.
    from app.models.user import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
