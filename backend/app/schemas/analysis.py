"""
CodeLens AI — Analysis Schemas.

Response schemas for analysis results: summary, file metrics, debt items,
dependency findings, modernisation score, and repository structure.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Analysis ─────────────────────────────────────────────────────────────
class AnalysisResponse(BaseModel):
    """Full analysis run record."""

    id: uuid.UUID
    project_id: uuid.UUID
    commit_sha: str | None = None
    status: str
    summary: dict[str, Any] | None = None
    overall_score: float | None = None
    grade: str | None = None
    sub_scores: dict[str, Any] | None = None
    language_breakdown: dict[str, Any] | None = None
    duration_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AnalysisSummaryResponse(BaseModel):
    """Condensed analysis summary for the dashboard."""

    id: uuid.UUID
    status: str
    overall_score: float | None = None
    grade: str | None = None
    summary: dict[str, Any] | None = None
    language_breakdown: dict[str, Any] | None = None
    duration_seconds: float | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── File Metrics ─────────────────────────────────────────────────────────
class FileMetricResponse(BaseModel):
    """Per-file quality metrics."""

    id: uuid.UUID
    file_path: str
    language: str | None = None
    loc: int
    complexity: float
    max_nesting: int
    function_count: int
    class_count: int
    comment_ratio: float
    issues: dict[str, Any] | None = None
    risk_level: str

    model_config = {"from_attributes": True}


# ── Debt Items ───────────────────────────────────────────────────────────
class DebtItemResponse(BaseModel):
    """A single technical-debt finding."""

    id: uuid.UUID
    category: str
    severity: str
    title: str
    description: str
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    suggestion: str | None = None
    estimated_hours: float | None = None

    model_config = {"from_attributes": True}


# ── Dependency Findings ──────────────────────────────────────────────────
class DependencyFindingResponse(BaseModel):
    """Per-package dependency health."""

    id: uuid.UUID
    package_name: str
    current_version: str | None = None
    latest_version: str | None = None
    ecosystem: str
    days_behind: int
    is_deprecated: bool
    vulnerability_count: int
    vulnerabilities: dict[str, Any] | None = None
    risk_level: str
    license: str | None = None

    model_config = {"from_attributes": True}


# ── Score ────────────────────────────────────────────────────────────────
class ScoreResponse(BaseModel):
    """Modernisation readiness score breakdown."""

    id: uuid.UUID
    analysis_id: uuid.UUID
    overall_score: float
    grade: str
    code_health: float
    dependency_health: float
    architecture_quality: float
    test_coverage: float
    documentation: float
    infrastructure_readiness: float
    security_posture: float
    priority_areas: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


# ── Repository Structure ────────────────────────────────────────────────
class StructureNode(BaseModel):
    """A single node in the repository file tree."""

    name: str
    path: str
    type: str = Field(description="'file' or 'directory'.")
    language: str | None = None
    loc: int | None = None
    children: list["StructureNode"] | None = None


class StructureResponse(BaseModel):
    """Full repository file tree structure."""

    root: StructureNode
    total_files: int
    total_directories: int
