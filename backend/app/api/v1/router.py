"""
API v1 Router
=============

Aggregates all v1 route modules into a single router mounted at ``/api/v1``.
"""

from fastapi import APIRouter

from app.api.v1.routes import auth, projects, analysis, recommendations, reports, jobs, webhooks

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(analysis.router, tags=["Analysis"])
router.include_router(recommendations.router, tags=["Recommendations"])
router.include_router(reports.router, tags=["Reports"])
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
router.include_router(webhooks.router, tags=["Webhooks"])
