"""
Analysis Models
===============

Contains four tightly related models that store the *results* of a single
analysis run:

* :class:`Analysis` — top-level analysis record (one per run).
* :class:`FileMetric` — per-file structural metrics extracted via tree-sitter.
* :class:`DebtItem` — individual technical-debt findings.
* :class:`DependencyFinding` — per-package health / risk data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════════════════════════


class Analysis(Base):
    """
    A single analysis run against a project.

    Every time a user triggers analysis, a new ``Analysis`` row is created.
    The latest completed one is shown on the dashboard.
    """

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")

    # High-level summary stored as JSON for flexibility.
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(2), nullable=True)
    sub_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    language_breakdown: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────
    project = relationship("Project", back_populates="analyses")
    file_metrics = relationship(
        "FileMetric", back_populates="analysis", cascade="all, delete-orphan"
    )
    debt_items = relationship(
        "DebtItem", back_populates="analysis", cascade="all, delete-orphan"
    )
    dependency_findings = relationship(
        "DependencyFinding",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    recommendations = relationship(
        "Recommendation",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    score = relationship(
        "ModernizationScore",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FileMetric
# ═══════════════════════════════════════════════════════════════════════════════


class FileMetric(Base):
    """
    Structural metrics for a single source file, extracted by the
    tree-sitter AST parser.
    """

    __tablename__ = "file_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    loc: Mapped[int] = mapped_column(Integer, default=0)
    complexity: Mapped[int] = mapped_column(Integer, default=0)
    max_nesting: Mapped[int] = mapped_column(Integer, default=0)
    function_count: Mapped[int] = mapped_column(Integer, default=0)
    class_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_ratio: Mapped[float] = mapped_column(Float, default=0.0)

    # Per-file issues as a JSON array (e.g. rule violations found).
    issues: Mapped[list | None] = mapped_column(JSONB, default=list)
    risk_level: Mapped[str] = mapped_column(String(10), default="low")

    # ── Relationships ────────────────────────────────────────────────────
    analysis = relationship("Analysis", back_populates="file_metrics")


# ═══════════════════════════════════════════════════════════════════════════════
# DebtItem
# ═══════════════════════════════════════════════════════════════════════════════


class DebtItem(Base):
    """
    A single technical-debt finding (code smell, anti-pattern, or security
    issue) detected by the rule engine or AI pipeline.
    """

    __tablename__ = "debt_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Category: complexity | duplication | style | security | architecture | documentation
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    # Severity: low | medium | high | critical
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────
    analysis = relationship("Analysis", back_populates="debt_items")


# ═══════════════════════════════════════════════════════════════════════════════
# DependencyFinding
# ═══════════════════════════════════════════════════════════════════════════════


class DependencyFinding(Base):
    """
    Health and risk data for a single third-party package discovered in the
    repository (e.g. from ``package.json`` or ``requirements.txt``).
    """

    __tablename__ = "dependency_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    latest_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # Ecosystem: npm | pip | maven | nuget | cargo | go
    ecosystem: Mapped[str | None] = mapped_column(String(20), nullable=True)
    days_behind: Mapped[int] = mapped_column(Integer, default=0)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    vulnerability_count: Mapped[int] = mapped_column(Integer, default=0)
    vulnerabilities: Mapped[list | None] = mapped_column(JSONB, default=list)
    risk_level: Mapped[str] = mapped_column(String(10), default="low")
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    analysis = relationship("Analysis", back_populates="dependency_findings")
