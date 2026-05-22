"""
Recommendation Routes
=====================

Serves AI-generated modernization recommendations and on-demand refactoring.

Endpoints:
    GET  /projects/{id}/recommendations              — All recommendations.
    GET  /projects/{id}/recommendations/{rec_id}      — Single detail.
    POST /projects/{id}/recommendations/{rec_id}/refactor — AI refactoring.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationResponse,
    RefactorRequest,
    RefactorResponse,
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=RecommendationListResponse,
)
async def list_recommendations(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated AI recommendations for the latest analysis."""
    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    if proj.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = (
        await db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id, Analysis.status == "completed")
            .order_by(Analysis.completed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if analysis is None:
        return RecommendationListResponse(recommendations=[], total=0, by_priority={})

    where = Recommendation.analysis_id == analysis.id

    total = (await db.execute(
        select(func.count()).select_from(Recommendation).where(where)
    )).scalar() or 0

    pri_rows = (await db.execute(
        select(Recommendation.priority, func.count(Recommendation.id).label("cnt"))
        .where(where)
        .group_by(Recommendation.priority)
    )).all()
    by_priority = {r.priority: r.cnt for r in pri_rows}

    result = await db.execute(
        select(Recommendation).where(where)
        .order_by(Recommendation.impact_score.desc().nullslast())
        .offset(skip).limit(limit)
    )
    recs = [RecommendationResponse.model_validate(r) for r in result.scalars().all()]

    return RecommendationListResponse(
        recommendations=recs, total=total, by_priority=by_priority
    )


@router.get(
    "/projects/{project_id}/recommendations/{rec_id}",
    response_model=RecommendationResponse,
)
async def get_recommendation(
    project_id: uuid.UUID,
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single recommendation by ID."""
    # Ownership check.
    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    if proj.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Recommendation).where(Recommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return RecommendationResponse.model_validate(rec)


@router.post(
    "/projects/{project_id}/recommendations/{rec_id}/refactor",
    response_model=RefactorResponse,
)
async def refactor_recommendation(
    project_id: uuid.UUID,
    rec_id: uuid.UUID,
    payload: RefactorRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI-powered refactored code for a recommendation.

    This calls the AI pipeline on-demand to produce a before/after diff.
    """
    # Ownership check.
    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    if proj.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Recommendation).where(Recommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # On-demand AI refactoring is not yet implemented; returns stored code or a
    # placeholder. Wire up ai_pipeline.generate_refactoring() here when ready.
    return RefactorResponse(
        recommendation_id=rec.id,
        file_path=payload.file_path if payload else None,
        language=None,
        before_code=rec.before_code or "// Original code",
        after_code=rec.after_code or "// Refactored code — AI generation pending",
        explanation=rec.rationale or "AI refactoring will be generated on demand.",
    )
