"""
CodeLens AI — Project Model.

A *project* represents a single GitHub repository that the user has imported
for analysis.  It tracks the repository URL, detected languages, status, and
high-level statistics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """A GitHub repository imported for code modernisation analysis.

    Lifecycle::

        pending → analyzing → completed
                            ↘ failed
    """

    __tablename__ = "projects"

    # ── Primary key ──────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Owner ────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the owning user.",
    )

    # ── Repository metadata ──────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable project name (defaults to repo name).",
    )
    repo_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full HTTPS clone URL.",
    )
    repo_full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="GitHub 'owner/repo' slug.",
    )
    default_branch: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="main",
        doc="Default branch used for analysis.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Short description of the project.",
    )

    # ── Analysis summary fields ──────────────────────────────────────────
    detected_languages: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Mapping of detected languages → file count.",
    )
    total_files: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Total source files discovered.",
    )
    total_loc: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Total lines of code across all files.",
    )

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        doc="Current analysis status: pending | analyzing | completed | failed.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    last_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the most recent analysis completed.",
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
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="projects",
    )
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        "Analysis",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # noqa: D401
        """Readable representation for debugging."""
        return f"<Project id={self.id!s} name={self.name!r} status={self.status!r}>"
