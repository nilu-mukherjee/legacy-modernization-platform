"""
CodeLens AI — Analysis Models.

Contains four tightly related models that store the results of a single
analysis run:

* :class:`Analysis` — top-level run record with status, score, and timing.
* :class:`FileMetric` — per-file code-quality metrics.
* :class:`DebtItem` — individual technical-debt findings.
* :class:`DependencyFinding` — per-package dependency health results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ═══════════════════════════════════════════════════════════════════════════
# Analysis — top-level run
# ═══════════════════════════════════════════════════════════════════════════
class Analysis(Base):
    """A single analysis run for a project.

    Each time a project is (re-)analysed a new ``Analysis`` row is created.
    The most recent completed row represents the current state of the codebase.
    """

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Git context ──────────────────────────────────────────────────────
    commit_sha: Mapped[str | None] = mapped_column(
        String(40), nullable=True, doc="HEAD commit SHA at time of analysis.",
    )

    # ── Status & results ─────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        doc="pending | running | completed | failed",
    )
    summary: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, doc="AI-generated executive summary.",
    )
    overall_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Composite modernisation score (0–100).",
    )
    grade: Mapped[str | None] = mapped_column(
        String(2), nullable=True, doc="Letter grade derived from overall_score.",
    )
    sub_scores: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, doc="Breakdown of sub-dimension scores.",
    )
    language_breakdown: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, doc="Lines-of-code per language.",
    )

    # ── Timing ───────────────────────────────────────────────────────────
    duration_seconds: Mapped[float | None] = mapped_column(
        Float, nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="analyses",
    )
    file_metrics: Mapped[list["FileMetric"]] = relationship(
        "FileMetric", back_populates="analysis", cascade="all, delete-orphan",
    )
    debt_items: Mapped[list["DebtItem"]] = relationship(
        "DebtItem", back_populates="analysis", cascade="all, delete-orphan",
    )
    dependency_findings: Mapped[list["DependencyFinding"]] = relationship(
        "DependencyFinding", back_populates="analysis", cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="analysis", cascade="all, delete-orphan",
    )
    score: Mapped["ModernizationScore | None"] = relationship(  # noqa: F821
        "ModernizationScore", back_populates="analysis", uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<Analysis id={self.id!s} status={self.status!r}>"


# ═══════════════════════════════════════════════════════════════════════════
# FileMetric — per-file quality metrics
# ═══════════════════════════════════════════════════════════════════════════
class FileMetric(Base):
    """Per-file code-quality metrics extracted by the AST parser.

    Stores complexity, LOC, function/class counts, and identified issues
    for a single source file.
    """

    __tablename__ = "file_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── File info ────────────────────────────────────────────────────────
    file_path: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Path relative to the repository root.",
    )
    language: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )

    # ── Metrics ──────────────────────────────────────────────────────────
    loc: Mapped[int] = mapped_column(Integer, default=0, doc="Lines of code.")
    complexity: Mapped[float] = mapped_column(
        Float, default=0.0, doc="Average cyclomatic complexity.",
    )
    max_nesting: Mapped[int] = mapped_column(
        Integer, default=0, doc="Maximum nesting depth.",
    )
    function_count: Mapped[int] = mapped_column(Integer, default=0)
    class_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_ratio: Mapped[float] = mapped_column(
        Float, default=0.0, doc="Comments / total lines (0–1).",
    )

    # ── Issues & risk ────────────────────────────────────────────────────
    issues: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, doc="List of per-file issues (warnings).",
    )
    risk_level: Mapped[str] = mapped_column(
        String(20), default="low", doc="low | medium | high | critical",
    )

    # ── Relationship ─────────────────────────────────────────────────────
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="file_metrics")

    def __repr__(self) -> str:  # noqa: D401
        return f"<FileMetric file={self.file_path!r} risk={self.risk_level!r}>"


# ═══════════════════════════════════════════════════════════════════════════
# DebtItem — technical-debt findings
# ═══════════════════════════════════════════════════════════════════════════
class DebtItem(Base):
    """A single technical-debt issue detected in the codebase.

    Debt items are categorised (complexity, style, architecture, security, …)
    and assigned an estimated remediation time.
    """

    __tablename__ = "debt_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Classification ───────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(
        String(50), nullable=False,
        doc="complexity | style | architecture | security | documentation | testing",
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium",
        doc="low | medium | high | critical",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Location ─────────────────────────────────────────────────────────
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Remediation ──────────────────────────────────────────────────────
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Relationship ─────────────────────────────────────────────────────
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="debt_items")

    def __repr__(self) -> str:  # noqa: D401
        return f"<DebtItem title={self.title!r} severity={self.severity!r}>"


# ═══════════════════════════════════════════════════════════════════════════
# DependencyFinding — per-package dependency health
# ═══════════════════════════════════════════════════════════════════════════
class DependencyFinding(Base):
    """Health status of a single dependency package.

    Includes version lag, deprecation status, known vulnerabilities, and
    licence information.
    """

    __tablename__ = "dependency_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Package info ─────────────────────────────────────────────────────
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latest_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ecosystem: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="npm | pypi | maven | etc.",
    )

    # ── Health indicators ────────────────────────────────────────────────
    days_behind: Mapped[int] = mapped_column(Integer, default=0)
    is_deprecated: Mapped[bool] = mapped_column(default=False)
    vulnerability_count: Mapped[int] = mapped_column(Integer, default=0)
    vulnerabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Risk & licence ───────────────────────────────────────────────────
    risk_level: Mapped[str] = mapped_column(
        String(20), default="low", doc="low | medium | high | critical",
    )
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Relationship ─────────────────────────────────────────────────────
    analysis: Mapped["Analysis"] = relationship(
        "Analysis", back_populates="dependency_findings",
    )

    def __repr__(self) -> str:  # noqa: D401
        return (
            f"<DependencyFinding pkg={self.package_name!r} "
            f"risk={self.risk_level!r}>"
        )
