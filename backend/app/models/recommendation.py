"""
CodeLens AI — Recommendation Model.

Stores AI-generated modernisation recommendations linked to an analysis run.
Each recommendation includes the rationale, implementation steps, and
optional before/after code snippets for refactoring.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recommendation(Base):
    """An AI-generated modernisation recommendation.

    Recommendations are produced by the AI pipeline during analysis and
    can later be used to generate concrete refactored code snippets.
    """

    __tablename__ = "recommendations"

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
        doc="refactoring | dependency | architecture | security | testing | documentation",
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=3,
        doc="1 (highest) to 5 (lowest).",
    )

    # ── Content ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Why this change is recommended.",
    )
    implementation_steps: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Step-by-step instructions (Markdown).",
    )

    # ── Effort estimation ────────────────────────────────────────────────
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Expected improvement impact (0–100).",
    )

    # ── Affected files & code ────────────────────────────────────────────
    affected_files: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, doc="List of file paths affected by this change.",
    )
    before_code: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Original code snippet.",
    )
    after_code: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Suggested refactored code snippet.",
    )

    # ── Relationship ─────────────────────────────────────────────────────
    analysis: Mapped["Analysis"] = relationship(  # noqa: F821
        "Analysis", back_populates="recommendations",
    )

    def __repr__(self) -> str:  # noqa: D401
        return f"<Recommendation title={self.title!r} priority={self.priority}>"
