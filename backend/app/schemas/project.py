"""
Project Schemas
===============

Request and response models for project CRUD and analysis triggers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from app.schemas.common import OrmBase


class ProjectCreate(BaseModel):
    """Request body for ``POST /projects``."""

    repo_url: str  # GitHub repository URL
    name: Optional[str] = None  # Defaults to repo name if omitted


class ProjectResponse(OrmBase):
    """Full project detail returned by the API."""

    id: UUID
    user_id: UUID
    name: str
    repo_url: str
    repo_full_name: Optional[str]
    default_branch: str
    description: Optional[str]
    detected_languages: Optional[dict]
    total_files: int
    total_loc: int
    status: str
    last_analyzed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ProjectCreateResponse(OrmBase):
    """Returned after creating a project — includes the triggered job ID."""

    id: UUID
    name: str
    repo_url: str
    status: str
    job_id: Optional[UUID] = None
    created_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    projects: list[ProjectResponse]
    total: int
