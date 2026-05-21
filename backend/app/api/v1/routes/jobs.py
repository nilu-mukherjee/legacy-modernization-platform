"""
Job Routes
==========

Endpoints for polling background job status and progress.

Endpoints:
    GET /jobs/{id}             — Single job status.
    GET /projects/{id}/jobs    — All jobs for a project.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.schemas.job import JobDetailResponse, JobResponse, JobStepResponse

router = APIRouter()

# The fixed pipeline steps and their progress thresholds.
_PIPELINE_STEPS = [
    ("Cloning repository", 15),
    ("Scanning files", 25),
    ("Parsing source code", 45),
    ("Computing metrics", 60),
    ("Analyzing dependencies", 70),
    ("Running AI analysis", 90),
    ("Calculating score", 100),
]


def _build_steps(progress: int) -> list[JobStepResponse]:
    """
    Derive step statuses from the overall progress percentage.

    Each step is marked completed if progress >= its threshold, running if
    progress is between the previous and current threshold, else pending.
    """
    steps: list[JobStepResponse] = []
    prev = 0
    for name, threshold in _PIPELINE_STEPS:
        if progress >= threshold:
            status = "completed"
        elif progress >= prev:
            status = "running"
        else:
            status = "pending"
        steps.append(JobStepResponse(name=name, status=status))
        prev = threshold
    return steps


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the status and progress of a background job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify ownership via project.
    proj = await db.execute(
        select(Project).where(
            Project.id == job.project_id, Project.user_id == current_user.id
        )
    )
    if proj.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Job not found")

    response = JobDetailResponse.model_validate(job)
    response.steps = _build_steps(job.progress)
    return response


@router.get("")
async def list_project_jobs(
    project_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all jobs, optionally filtered by project_id (query param)."""
    if project_id:
        proj = await db.execute(
            select(Project).where(
                Project.id == project_id, Project.user_id == current_user.id
            )
        )
        if proj.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Project not found")

        result = await db.execute(
            select(Job)
            .where(Job.project_id == project_id)
            .order_by(Job.started_at.desc().nullslast())
        )
    else:
        # All jobs for user's projects.
        result = await db.execute(
            select(Job)
            .join(Project, Job.project_id == Project.id)
            .where(Project.user_id == current_user.id)
            .order_by(Job.started_at.desc().nullslast())
            .limit(50)
        )

    jobs = [JobResponse.model_validate(j) for j in result.scalars().all()]
    return {"jobs": jobs, "total": len(jobs)}
