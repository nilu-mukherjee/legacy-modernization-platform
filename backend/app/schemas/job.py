"""
Job Schemas
===========

Response models for background job status and progress tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmBase


class JobStepResponse(BaseModel):
    """A single step in the analysis pipeline."""

    name: str
    status: str  # completed | running | pending


class JobResponse(OrmBase):
    """Background job status and progress."""

    id: UUID
    project_id: UUID
    job_type: str
    status: str
    progress: int
    current_step: Optional[str]
    error_message: Optional[str]
    result_metadata: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class JobDetailResponse(JobResponse):
    """Extended job response with pipeline step breakdown."""

    steps: list[JobStepResponse] = []
