"""
Recommendation Model
====================

Stores AI-generated modernization recommendations produced by the synthesis
stage of the AI pipeline.  Each recommendation belongs to a single
:class:`~app.models.analysis.Analysis`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recommendation(Base):
    """
    A single AI-generated modernization recommendation.

    Categories: upgrade | refactor | security | performance | testing | architecture
    Priorities: low | medium | high | critical
    """

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_steps: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    estimated_hours: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # List of file paths affected by this recommendation.
    affected_files: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Optional before/after code snippets (populated by the AI).
    before_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    analysis = relationship("Analysis", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation [{self.priority}] {self.title[:40]}>"
