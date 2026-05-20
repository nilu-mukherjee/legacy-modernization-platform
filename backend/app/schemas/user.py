"""
CodeLens AI — User Schemas.

Request/response schemas for user-related endpoints (GitHub OAuth sync,
profile retrieval).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserSync(BaseModel):
    """Payload sent by the frontend after a successful GitHub OAuth flow.

    The backend uses this to create-or-update the local ``User`` record and
    encrypt the access token for later use.
    """

    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    github_id: int = Field(description="GitHub numeric user ID.")
    github_access_token: str = Field(
        description="Raw GitHub OAuth access token (will be encrypted before storage).",
    )


class UserCreate(BaseModel):
    """Internal schema used when inserting a new user row.

    Equivalent to :class:`UserSync` but with the token already encrypted.
    """

    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    github_id: int
    github_access_token: str | None = None  # Encrypted form


class UserResponse(BaseModel):
    """Public representation of a user returned by the API.

    The ``github_access_token`` is **never** exposed to the client.
    """

    id: uuid.UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    github_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
