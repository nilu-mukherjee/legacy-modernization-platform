"""
Auth Routes
===========

Handles GitHub OAuth user synchronisation and profile retrieval.

Endpoints:
    POST /auth/sync  — Upsert user from GitHub OAuth.
    GET  /auth/me    — Get authenticated user profile.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    get_encryptor,
)
from app.models.user import User
from app.schemas.user import UserResponse, UserSync, UserSyncResponse

router = APIRouter()


@router.post("/sync", response_model=UserSyncResponse, status_code=200)
async def sync_user(payload: UserSync, db: AsyncSession = Depends(get_db)):
    """
    Upsert a user from a GitHub OAuth callback.

    Called by the frontend after successful GitHub authentication. Creates
    the user if they don't exist, or updates their token and profile if
    they do.  Returns a JWT for subsequent API calls.
    """
    # Look up by github_id first, then by email.
    result = await db.execute(
        select(User).where(User.github_id == payload.github_id)
    )
    user = result.scalar_one_or_none()

    encryptor = get_encryptor()
    encrypted_token = encryptor.encrypt(payload.access_token)

    if user is None:
        # Create new user — guard against concurrent sync calls on the same email.
        user = User(
            email=payload.email,
            name=payload.name,
            avatar_url=payload.avatar_url,
            github_id=payload.github_id,
            github_access_token=encrypted_token,
        )
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result2 = await db.execute(
                select(User).where(User.email == payload.email)
            )
            user = result2.scalar_one_or_none()
            if user is None:
                raise
            user.github_id = payload.github_id
            user.name = payload.name or user.name
            user.avatar_url = payload.avatar_url or user.avatar_url
            user.github_access_token = encrypted_token
    else:
        # Update existing user profile + token.
        user.name = payload.name or user.name
        user.avatar_url = payload.avatar_url or user.avatar_url
        user.email = payload.email
        user.github_access_token = encrypted_token

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return UserSyncResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
        token=token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
