"""widen dependency_findings varchar columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "dependency_findings", "current_version",
        existing_type=sa.String(50), type_=sa.String(200), nullable=True,
    )
    op.alter_column(
        "dependency_findings", "latest_version",
        existing_type=sa.String(50), type_=sa.String(200), nullable=True,
    )
    op.alter_column(
        "dependency_findings", "license",
        existing_type=sa.String(100), type_=sa.String(500), nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "dependency_findings", "license",
        existing_type=sa.String(500), type_=sa.String(100), nullable=True,
    )
    op.alter_column(
        "dependency_findings", "latest_version",
        existing_type=sa.String(200), type_=sa.String(50), nullable=True,
    )
    op.alter_column(
        "dependency_findings", "current_version",
        existing_type=sa.String(200), type_=sa.String(50), nullable=True,
    )
