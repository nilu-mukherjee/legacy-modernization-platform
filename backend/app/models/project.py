"""
Project Model
=============

A project represents a single GitHub repository that the user has submitted
for modernization analysis.  It tracks metadata discovered during ingestion
and the current analysis status.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """A GitHub repository submitted for analysis."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_url: Mapped[str] = mapped_column(Text, nullable=False)
    repo_full_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    default_branch: Mapped[str] = mapped_column(
        String(100), default="main"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Discovered during ingestion — e.g. {"python": 45, "javascript": 12}
    detected_languages: Mapped[dict | None] = mapped_column(
        JSONB, default=dict
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_loc: Mapped[int] = mapped_column(Integer, default=0)

    # Lifecycle: pending → analyzing → completed | failed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    last_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────────────
    owner = relationship("User", back_populates="projects")
    analyses = relationship(
        "Analysis", back_populates="project", cascade="all, delete-orphan"
    )
    jobs = relationship(
        "Job", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} ({self.status})>"
