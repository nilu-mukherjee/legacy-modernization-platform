"""
CodeLens AI — Modernization Score Model.

Stores the composite modernisation health score for an analysis run.
The score is broken into seven sub-dimensions that together produce a
weighted overall grade.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ModernizationScore(Base):
    """Composite modernisation readiness score for a project analysis.

    There is exactly **one** score row per analysis (enforced by the unique
    constraint on ``analysis_id``).
    """

    __tablename__ = "modernization_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One score per analysis
        index=True,
    )

    # ── Overall ──────────────────────────────────────────────────────────
    overall_score: Mapped[float] = mapped_column(
        Float, nullable=False, doc="Weighted composite score (0–100).",
    )
    grade: Mapped[str] = mapped_column(
        String(2), nullable=False, doc="Letter grade: A, B, C, D, or F.",
    )

    # ── Sub-dimensions (each 0–100) ─────────────────────────────────────
    code_health: Mapped[float] = mapped_column(Float, default=0.0)
    dependency_health: Mapped[float] = mapped_column(Float, default=0.0)
    architecture_quality: Mapped[float] = mapped_column(Float, default=0.0)
    test_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    documentation: Mapped[float] = mapped_column(Float, default=0.0)
    infrastructure_readiness: Mapped[float] = mapped_column(Float, default=0.0)
    security_posture: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Priority areas ───────────────────────────────────────────────────
    priority_areas: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        doc="Ordered list of improvement areas to focus on.",
    )

    # ── Relationship ─────────────────────────────────────────────────────
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis", back_populates="score",
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<ModernizationScore grade={self.grade!r} score={self.overall_score}>"
