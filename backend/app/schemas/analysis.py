"""
Analysis Schemas
================

Response models for analysis results: summaries, file metrics, debt items,
dependency findings, scores, and repository structure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmBase


# ── Analysis Summary ─────────────────────────────────────────────────────────


class AnalysisResponse(OrmBase):
    """Top-level analysis summary."""

    id: UUID
    project_id: UUID
    commit_sha: Optional[str]
    status: str
    overall_score: Optional[float]
    grade: Optional[str]
    summary: Optional[dict]
    sub_scores: Optional[dict]
    language_breakdown: Optional[dict]
    duration_seconds: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]


# ── Score ─────────────────────────────────────────────────────────────────────


class ScoreResponse(OrmBase):
    """Modernization readiness score breakdown."""

    overall_score: float
    grade: str
    sub_scores: dict  # code_health, dependency_health, etc.
    priority_areas: Optional[list]


# ── File Metrics ─────────────────────────────────────────────────────────────


class FileMetricResponse(OrmBase):
    """Per-file structural metrics."""

    file_path: str
    language: Optional[str]
    loc: int
    complexity: int
    max_nesting: int
    function_count: int
    class_count: int
    comment_ratio: float
    risk_level: str
    issues: Optional[list]


class FileMetricListResponse(BaseModel):
    """Paginated file metrics."""

    files: list[FileMetricResponse]
    total: int


# ── Debt Items ───────────────────────────────────────────────────────────────


class DebtItemResponse(OrmBase):
    """A single technical debt finding."""

    id: UUID
    category: str
    severity: str
    title: str
    description: Optional[str]
    file_path: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    suggestion: Optional[str]
    estimated_hours: Optional[float]


class DebtListResponse(BaseModel):
    """All debt items with summary counts."""

    debt_items: list[DebtItemResponse]
    total: int
    by_severity: dict  # {"critical": 5, "high": 12, ...}


# ── Dependency Findings ──────────────────────────────────────────────────────


class DependencyFindingResponse(OrmBase):
    """Health data for a single dependency."""

    id: UUID
    package_name: str
    current_version: Optional[str]
    latest_version: Optional[str]
    ecosystem: Optional[str]
    days_behind: int
    is_deprecated: bool
    vulnerability_count: int
    vulnerabilities: Optional[list]
    risk_level: str
    license: Optional[str]


class DependencyListResponse(BaseModel):
    """All dependencies with summary."""

    dependencies: list[DependencyFindingResponse]
    total: int
    summary: dict


# ── Repository Structure ─────────────────────────────────────────────────────


class FileNode(BaseModel):
    """A single node (file or directory) in the repository tree."""

    name: str
    type: str  # "file" | "directory"
    language: Optional[str] = None
    loc: Optional[int] = None
    risk_level: Optional[str] = None
    children: Optional[list["FileNode"]] = None


class StructureResponse(BaseModel):
    """Repository file tree."""

    tree: FileNode
