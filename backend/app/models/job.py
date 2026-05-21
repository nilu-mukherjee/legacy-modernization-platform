"""
Job Model
=========

Tracks the lifecycle and progress of background analysis jobs.  The ARQ
worker updates ``progress`` and ``current_step`` as it works; the frontend
polls the ``/jobs/{id}`` endpoint for real-time feedback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    """
    A background analysis job.

    Lifecycle: queued → running → completed | failed.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Job types: full_analysis | dependency_check | ai_recommendations
    job_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued")

    # 0-100 progress percentage, updated by the worker.
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Arbitrary metadata about the result (e.g. analysis_id).
    result_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────
    project = relationship("Project", back_populates="jobs")

    def __repr__(self) -> str:
        return f"<Job {self.job_type} {self.status} ({self.progress}%)>"
