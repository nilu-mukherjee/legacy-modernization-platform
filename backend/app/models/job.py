"""
CodeLens AI — Job Model.

Tracks background jobs (typically kicked off via ARQ) that perform
long-running tasks such as repository analysis.  The frontend polls the
job status to display real-time progress.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    """A background task record.

    Created when a user triggers an analysis.  The ARQ worker updates the
    ``progress``, ``current_step``, and ``status`` fields as the pipeline
    executes.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Job metadata ─────────────────────────────────────────────────────
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full_analysis",
        doc="Type of job (e.g. full_analysis, re_analysis).",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued",
        doc="queued | running | completed | failed",
    )
    progress: Mapped[float] = mapped_column(
        Float, default=0.0,
        doc="Progress percentage (0–100).",
    )
    current_step: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        doc="Human-readable label for the current pipeline step.",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="Error details if the job failed.",
    )
    result_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        doc="Arbitrary result data stored upon completion.",
    )

    # ── Timing ───────────────────────────────────────────────────────────
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="jobs",
    )

    def __repr__(self) -> str:  # noqa: D401
        return (
            f"<Job id={self.id!s} type={self.job_type!r} "
            f"status={self.status!r} progress={self.progress:.0f}%>"
        )
