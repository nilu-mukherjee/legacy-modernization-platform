"""
User Schemas
============

Request and response models for user-related endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.common import OrmBase


class UserSync(BaseModel):
    """Payload sent by the frontend after GitHub OAuth to sync the user."""

    github_id: str
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: str  # GitHub OAuth access token (will be encrypted)


class UserResponse(OrmBase):
    """Public user profile returned by ``GET /auth/me``."""

    id: UUID
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class UserSyncResponse(UserResponse):
    """Response from ``POST /auth/sync`` — includes a JWT for the frontend."""

    token: str
