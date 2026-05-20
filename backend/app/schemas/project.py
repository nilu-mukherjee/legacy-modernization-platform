"""
CodeLens AI — Project Schemas.

Request/response schemas for project CRUD operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ProjectCreate(BaseModel):
    """Payload for creating a new project from a GitHub repository URL."""

    repo_url: HttpUrl = Field(
        description="Full HTTPS URL to the GitHub repository.",
        examples=["https://github.com/owner/repo"],
    )
    name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional display name. Defaults to the repo name.",
    )


class ProjectUpdate(BaseModel):
    """Payload for updating mutable project fields."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    default_branch: str | None = None


class ProjectResponse(BaseModel):
    """Full project representation returned by the API."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    repo_url: str
    repo_full_name: str | None = None
    default_branch: str
    description: str | None = None
    detected_languages: dict[str, Any] | None = None
    total_files: int
    total_loc: int
    status: str
    last_analyzed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Lightweight project summary used in list endpoints."""

    id: uuid.UUID
    name: str
    repo_url: str
    repo_full_name: str | None = None
    status: str
    detected_languages: dict[str, Any] | None = None
    total_files: int
    total_loc: int
    last_analyzed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
