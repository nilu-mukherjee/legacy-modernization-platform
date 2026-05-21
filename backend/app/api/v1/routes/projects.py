"""
Project Routes
==============

CRUD operations for projects and analysis triggers.

Endpoints:
    GET    /projects              — List user's projects.
    POST   /projects              — Create project + trigger analysis.
    GET    /projects/{id}         — Get project detail.
    DELETE /projects/{id}         — Delete project.
    POST   /projects/{id}/analyze — Re-trigger analysis.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.job import Job
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectCreateResponse,
    ProjectListResponse,
    ProjectResponse,
)

router = APIRouter()

# Simple GitHub URL pattern for validation.
_GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[\w.\-]+/[\w.\-]+/?$", re.IGNORECASE
)


def _extract_repo_name(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    parts = url.rstrip("/").split("/")
    return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else url


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects owned by the authenticated user."""
    count_q = (
        select(func.count())
        .select_from(Project)
        .where(Project.user_id == current_user.id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    rows_q = (
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(rows_q)
    projects = [
        ProjectResponse.model_validate(p) for p in result.scalars().all()
    ]
    return ProjectListResponse(projects=projects, total=total)


@router.post("", response_model=ProjectCreateResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a project and enqueue a full analysis job.

    Validates the GitHub URL, creates the project record, and queues a
    background analysis job.
    """
    if not _GITHUB_URL_RE.match(payload.repo_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

    repo_full_name = _extract_repo_name(payload.repo_url)
    name = payload.name or repo_full_name.split("/")[-1]

    # Check for duplicates.
    existing = await db.execute(
        select(Project).where(
            Project.user_id == current_user.id,
            Project.repo_url == payload.repo_url,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This repository has already been added",
        )

    project = Project(
        user_id=current_user.id,
        name=name,
        repo_url=payload.repo_url,
        repo_full_name=repo_full_name,
        status="analyzing",
    )
    db.add(project)
    await db.flush()

    # Create a background job record.
    job = Job(
        project_id=project.id,
        job_type="full_analysis",
        status="queued",
    )
    db.add(job)
    await db.flush()

    # TODO: Enqueue the ARQ job here once the worker is wired up.
    # await arq_pool.enqueue_job("run_full_analysis", str(project.id), str(job.id))

    await db.commit()
    await db.refresh(project)

    return ProjectCreateResponse(
        id=project.id,
        name=project.name,
        repo_url=project.repo_url,
        status=project.status,
        job_id=job.id,
        created_at=project.created_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single project by ID (must belong to the authenticated user)."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all associated analysis data (cascading)."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/analyze", status_code=202)
async def re_analyze(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-trigger analysis for an existing project."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "analyzing"

    job = Job(project_id=project.id, job_type="full_analysis", status="queued")
    db.add(job)
    await db.flush()

    # TODO: Enqueue ARQ job.

    await db.commit()
    return {"message": "Analysis started", "job_id": str(job.id)}
