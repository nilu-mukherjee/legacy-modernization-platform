"""
CodeLens AI — User Model.

Stores authenticated GitHub users.  The ``github_access_token`` field is
Fernet-encrypted at rest (see :mod:`app.core.security.TokenEncryptor`).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Represents a registered CodeLens AI user.

    Users authenticate exclusively via GitHub OAuth.  Their GitHub access
    token is stored **encrypted** so that the platform can clone private
    repositories on their behalf.
    """

    __tablename__ = "users"

    # ── Primary key ──────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique user identifier (UUID v4).",
    )

    # ── Profile fields ───────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
        doc="User email from GitHub profile.",
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Display name.",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="URL of the user's GitHub avatar.",
    )

    # ── GitHub integration ───────────────────────────────────────────────
    github_id: Mapped[int] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
        doc="GitHub numeric user ID (stable across name changes).",
    )
    github_access_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Fernet-encrypted GitHub OAuth access token.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        doc="Row creation timestamp (UTC).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Last modification timestamp (UTC).",
    )

    # ── Relationships ────────────────────────────────────────────────────
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # noqa: D401
        """Readable representation for debugging."""
        return f"<User id={self.id!s} email={self.email!r}>"
