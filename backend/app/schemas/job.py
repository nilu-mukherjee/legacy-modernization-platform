"""
CodeLens AI — Job Schemas.

Response schemas for background job tracking endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobStepResponse(BaseModel):
    """Representation of a single pipeline step within a job.

    Used by the frontend to render a progress stepper.
    """

    name: str
    status: str  # pending | running | completed | failed
    progress: float = 0.0


class JobResponse(BaseModel):
    """Full background-job record."""

    id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: str
    progress: float
    current_step: str | None = None
    error_message: str | None = None
    result_metadata: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
