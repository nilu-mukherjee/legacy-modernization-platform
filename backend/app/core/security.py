"""
CodeLens AI — Security Utilities.

Provides three key capabilities:

1. **Token encryption** — Fernet symmetric encryption for storing GitHub
   access tokens at rest in the database.
2. **JWT creation / verification** — Stateless bearer tokens issued to
   authenticated users.
3. **Route protection** — A FastAPI dependency (``get_current_user``) that
   validates the JWT and resolves the current ``User`` record.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # Tokens valid for 7 days

# HTTPBearer scheme — extracts the ``Authorization: Bearer <token>`` header.
_bearer_scheme = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# Token Encryption (Fernet)
# ---------------------------------------------------------------------------
class TokenEncryptor:
    """Encrypts and decrypts sensitive tokens using Fernet symmetric encryption.

    The encryption key is read from ``settings.ENCRYPTION_KEY``.  If the key
    is not set, a warning is logged and a fresh key is generated (this is
    **only** acceptable during local development — in production the key must
    be stable across restarts so that existing encrypted values remain
    readable).
    """

    def __init__(self, key: str | None = None) -> None:
        """Initialise the encryptor.

        Args:
            key: A URL-safe base-64-encoded 32-byte key.  Defaults to
                 ``settings.ENCRYPTION_KEY``.
        """
        raw_key = key or settings.ENCRYPTION_KEY
        if not raw_key:
            # Generate an ephemeral key for dev convenience (not persistent!)
            raw_key = Fernet.generate_key().decode()
        self._fernet = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The value to encrypt.

        Returns:
            The encrypted ciphertext as a URL-safe base-64 string.
        """
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string.

        Args:
            ciphertext: A value previously produced by :meth:`encrypt`.

        Returns:
            The original plaintext.

        Raises:
            ValueError: If the ciphertext is invalid or the key has changed.
        """
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt token — key may have rotated") from exc


# Module-level singleton
token_encryptor = TokenEncryptor()


# ---------------------------------------------------------------------------
# JWT Helpers
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: uuid.UUID,
    email: str,
    extra_claims: dict | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        user_id: The authenticated user's UUID (stored as ``sub``).
        email: The user's email (included for convenience).
        extra_claims: Optional additional claims to embed in the payload.

    Returns:
        An encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "jti": str(uuid.uuid4()),  # Unique token identifier
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.AUTH_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The raw JWT string.

    Returns:
        The decoded payload dict.

    Raises:
        HTTPException: If the token is expired, malformed, or the signature
            does not match.
    """
    try:
        payload: dict = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        # Ensure the ``sub`` claim is present
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing 'sub' claim",
            )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# FastAPI Dependency — Route Protection
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency that authenticates the current request.

    Extracts the bearer token, validates the JWT, and returns the
    corresponding ``User`` ORM instance.

    Args:
        credentials: Bearer token extracted by ``HTTPBearer``.
        db: Async database session.

    Returns:
        The authenticated ``User`` model instance.

    Raises:
        HTTPException: 401 if the token is invalid or the user does not exist.
    """
    # Late import to avoid circular dependency (models → core → models)
    from app.models.user import User

    payload = verify_token(credentials.credentials)
    user_id = payload["sub"]

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for the provided token",
        )

    return user
