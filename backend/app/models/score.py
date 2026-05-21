"""
Modernization Score Model
=========================

Stores the composite readiness score (0-100) broken down into seven weighted
dimensions.  There is exactly **one** score row per :class:`Analysis`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ModernizationScore(Base):
    """
    Modernization readiness score for a single analysis run.

    Dimensions (weights):
        code_health (25%), dependency_health (20%), architecture_quality (15%),
        test_coverage (15%), documentation (10%), infrastructure_readiness (10%),
        security_posture (5%).

    Grades: A (≥80), B (60-79), C (40-59), D (20-39), F (<20).
    """

    __tablename__ = "modernization_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)

    # Individual dimension scores (0-100 each).
    code_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    dependency_health: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    architecture_quality: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    test_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    documentation: Mapped[float | None] = mapped_column(Float, nullable=True)
    infrastructure_readiness: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    security_posture: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Top areas that need attention, ordered by priority.
    priority_areas: Mapped[list | None] = mapped_column(JSONB, default=list)

    # ── Relationships ────────────────────────────────────────────────────
    analysis = relationship("Analysis", back_populates="score")

    def __repr__(self) -> str:
        return f"<ModernizationScore {self.grade} ({self.overall_score})>"
