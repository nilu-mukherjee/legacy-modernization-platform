"""
Analysis Routes
===============

Read-only endpoints that serve analysis results: summaries, scores,
file metrics, debt items, dependency findings, and repository structure.

All endpoints are scoped under ``/projects/{project_id}/analysis``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.analysis import Analysis, DebtItem, DependencyFinding, FileMetric
from app.models.project import Project
from app.models.score import ModernizationScore
from app.models.user import User
from app.schemas.analysis import (
    AnalysisResponse,
    DebtItemResponse,
    DebtListResponse,
    DependencyFindingResponse,
    DependencyListResponse,
    FileMetricListResponse,
    FileMetricResponse,
    ScoreResponse,
)

router = APIRouter()


async def _get_latest_analysis(
    project_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Analysis:
    """Helper: fetch the latest completed analysis for a project."""
    # Verify ownership.
    proj = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id
        )
    )
    if proj.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Analysis)
        .where(
            Analysis.project_id == project_id,
            Analysis.status == "completed",
        )
        .order_by(Analysis.completed_at.desc())
        .limit(1)
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="No completed analysis found")
    return analysis


@router.get(
    "/projects/{project_id}/analysis", response_model=AnalysisResponse
)
async def get_analysis(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest analysis summary for a project."""
    analysis = await _get_latest_analysis(project_id, current_user, db)
    return AnalysisResponse.model_validate(analysis)


@router.get(
    "/projects/{project_id}/analysis/score", response_model=ScoreResponse
)
async def get_score(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the modernization readiness score breakdown."""
    analysis = await _get_latest_analysis(project_id, current_user, db)
    result = await db.execute(
        select(ModernizationScore).where(
            ModernizationScore.analysis_id == analysis.id
        )
    )
    score = result.scalar_one_or_none()
    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")

    return ScoreResponse(
        overall_score=score.overall_score,
        grade=score.grade,
        sub_scores={
            "code_health": score.code_health,
            "dependency_health": score.dependency_health,
            "architecture_quality": score.architecture_quality,
            "test_coverage": score.test_coverage,
            "documentation": score.documentation,
            "infrastructure_readiness": score.infrastructure_readiness,
            "security_posture": score.security_posture,
        },
        priority_areas=score.priority_areas,
    )


@router.get(
    "/projects/{project_id}/analysis/files",
    response_model=FileMetricListResponse,
)
async def get_file_metrics(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    risk_level: str | None = None,
    language: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file-level metrics, with optional filtering and pagination."""
    analysis = await _get_latest_analysis(project_id, current_user, db)

    q = select(FileMetric).where(FileMetric.analysis_id == analysis.id)
    count_q = (
        select(func.count())
        .select_from(FileMetric)
        .where(FileMetric.analysis_id == analysis.id)
    )

    if risk_level:
        q = q.where(FileMetric.risk_level == risk_level)
        count_q = count_q.where(FileMetric.risk_level == risk_level)
    if language:
        q = q.where(FileMetric.language == language)
        count_q = count_q.where(FileMetric.language == language)

    total = (await db.execute(count_q)).scalar() or 0
    result = await db.execute(
        q.order_by(FileMetric.complexity.desc()).offset(skip).limit(limit)
    )
    files = [
        FileMetricResponse.model_validate(f) for f in result.scalars().all()
    ]
    return FileMetricListResponse(files=files, total=total)


@router.get(
    "/projects/{project_id}/analysis/debt", response_model=DebtListResponse
)
async def get_debt_items(
    project_id: uuid.UUID,
    severity: str | None = None,
    category: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all technical debt items for the latest analysis."""
    analysis = await _get_latest_analysis(project_id, current_user, db)

    q = select(DebtItem).where(DebtItem.analysis_id == analysis.id)
    if severity:
        q = q.where(DebtItem.severity == severity)
    if category:
        q = q.where(DebtItem.category == category)

    result = await db.execute(q.order_by(DebtItem.severity.desc()))
    items = [
        DebtItemResponse.model_validate(d) for d in result.scalars().all()
    ]

    # Build severity summary.
    by_severity: dict[str, int] = {}
    for item in items:
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

    return DebtListResponse(
        debt_items=items, total=len(items), by_severity=by_severity
    )


@router.get(
    "/projects/{project_id}/analysis/dependencies",
    response_model=DependencyListResponse,
)
async def get_dependencies(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dependency health findings for the latest analysis."""
    analysis = await _get_latest_analysis(project_id, current_user, db)

    result = await db.execute(
        select(DependencyFinding)
        .where(DependencyFinding.analysis_id == analysis.id)
        .order_by(DependencyFinding.days_behind.desc())
    )
    deps = [
        DependencyFindingResponse.model_validate(d)
        for d in result.scalars().all()
    ]

    by_risk: dict[str, int] = {}
    for d in deps:
        by_risk[d.risk_level] = by_risk.get(d.risk_level, 0) + 1

    return DependencyListResponse(
        dependencies=deps,
        total=len(deps),
        summary={
            "total_deps": len(deps),
            "outdated": sum(1 for d in deps if d.days_behind > 180),
            "deprecated": sum(1 for d in deps if d.is_deprecated),
            "vulnerable": sum(1 for d in deps if d.vulnerability_count > 0),
            "by_risk": by_risk,
        },
    )
