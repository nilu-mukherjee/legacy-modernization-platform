"""
Report Routes
=============

Generates and exports modernization reports.

Endpoints:
    GET /projects/{id}/report        — Full report data.
    GET /projects/{id}/report/export — Export as JSON download.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.score import ModernizationScore
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/report")
async def get_report(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assemble a full modernization report from the latest analysis.

    Combines project info, analysis summary, score breakdown,
    and recommendations into a single response.
    """
    proj = (
        await db.execute(
            select(Project).where(
                Project.id == project_id, Project.user_id == current_user.id
            )
        )
    ).scalar_one_or_none()
    if proj is None:
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
        raise HTTPException(status_code=404, detail="No completed analysis")

    score = (
        await db.execute(
            select(ModernizationScore).where(
                ModernizationScore.analysis_id == analysis.id
            )
        )
    ).scalar_one_or_none()

    return {
        "project": {
            "id": str(proj.id),
            "name": proj.name,
            "repo_url": proj.repo_url,
            "total_files": proj.total_files,
            "total_loc": proj.total_loc,
            "detected_languages": proj.detected_languages,
        },
        "analysis": {
            "id": str(analysis.id),
            "commit_sha": analysis.commit_sha,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
            "summary": analysis.summary,
            "duration_seconds": analysis.duration_seconds,
            "completed_at": (
                analysis.completed_at.isoformat() if analysis.completed_at else None
            ),
        },
        "score": {
            "overall_score": score.overall_score if score else None,
            "grade": score.grade if score else None,
            "code_health": score.code_health if score else None,
            "dependency_health": score.dependency_health if score else None,
            "architecture_quality": score.architecture_quality if score else None,
            "test_coverage": score.test_coverage if score else None,
            "documentation": score.documentation if score else None,
            "infrastructure_readiness": score.infrastructure_readiness if score else None,
            "security_posture": score.security_posture if score else None,
            "priority_areas": score.priority_areas if score else [],
        },
    }


@router.get("/projects/{project_id}/report/export")
async def export_report(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export the report as a downloadable JSON file."""
    # Reuse the report assembly logic.
    report_data = await get_report(project_id, current_user, db)

    return JSONResponse(
        content=report_data,
        headers={
            "Content-Disposition": f'attachment; filename="codelens-report-{project_id}.json"'
        },
    )
