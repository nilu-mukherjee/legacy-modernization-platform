"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-21

Creates all tables for the CodeLens AI platform:
    users, projects, jobs, analyses, file_metrics, debt_items,
    dependency_findings, recommendations, modernization_scores.

Also enables the uuid-ossp and pgvector PostgreSQL extensions.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("github_id", sa.String(50), nullable=True),
        sa.Column("github_access_token", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)

    # ── projects ──────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("repo_url", sa.Text, nullable=False),
        sa.Column("repo_full_name", sa.String(255), nullable=True),
        sa.Column("default_branch", sa.String(100), server_default="main", nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("detected_languages", postgresql.JSONB, nullable=True),
        sa.Column("total_files", sa.Integer, server_default="0", nullable=False),
        sa.Column("total_loc", sa.Integer, server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    # ── jobs ──────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued", nullable=False),
        sa.Column("progress", sa.Integer, server_default="0", nullable=False),
        sa.Column("current_step", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("result_metadata", postgresql.JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_project_id", "jobs", ["project_id"])

    # ── analyses ──────────────────────────────────────────────────────────
    op.create_table(
        "analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("status", sa.String(20), server_default="running", nullable=False),
        sa.Column("summary", postgresql.JSONB, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("grade", sa.String(2), nullable=True),
        sa.Column("sub_scores", postgresql.JSONB, nullable=True),
        sa.Column("language_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analyses_project_id", "analyses", ["project_id"])

    # ── file_metrics ──────────────────────────────────────────────────────
    op.create_table(
        "file_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("loc", sa.Integer, server_default="0", nullable=False),
        sa.Column("complexity", sa.Integer, server_default="0", nullable=False),
        sa.Column("max_nesting", sa.Integer, server_default="0", nullable=False),
        sa.Column("function_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("class_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("comment_ratio", sa.Float, server_default="0.0", nullable=False),
        sa.Column("issues", postgresql.JSONB, nullable=True),
        sa.Column("risk_level", sa.String(10), server_default="low", nullable=False),
    )
    op.create_index("ix_file_metrics_analysis_id", "file_metrics", ["analysis_id"])

    # ── debt_items ────────────────────────────────────────────────────────
    op.create_table(
        "debt_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_path", sa.Text, nullable=True),
        sa.Column("line_start", sa.Integer, nullable=True),
        sa.Column("line_end", sa.Integer, nullable=True),
        sa.Column("suggestion", sa.Text, nullable=True),
        sa.Column("estimated_hours", sa.Float, nullable=True),
    )
    op.create_index("ix_debt_items_analysis_id", "debt_items", ["analysis_id"])

    # ── dependency_findings ───────────────────────────────────────────────
    op.create_table(
        "dependency_findings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column("current_version", sa.String(50), nullable=True),
        sa.Column("latest_version", sa.String(50), nullable=True),
        sa.Column("ecosystem", sa.String(20), nullable=True),
        sa.Column("days_behind", sa.Integer, server_default="0", nullable=False),
        sa.Column("is_deprecated", sa.Boolean, server_default="false", nullable=False),
        sa.Column("vulnerability_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("vulnerabilities", postgresql.JSONB, nullable=True),
        sa.Column("risk_level", sa.String(10), server_default="low", nullable=False),
        sa.Column("license", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_dependency_findings_analysis_id", "dependency_findings", ["analysis_id"]
    )

    # ── recommendations ───────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("implementation_steps", sa.Text, nullable=True),
        sa.Column("estimated_hours", sa.Float, nullable=True),
        sa.Column("impact_score", sa.Float, nullable=True),
        sa.Column("affected_files", postgresql.JSONB, nullable=True),
        sa.Column("before_code", sa.Text, nullable=True),
        sa.Column("after_code", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_recommendations_analysis_id", "recommendations", ["analysis_id"]
    )

    # ── modernization_scores ──────────────────────────────────────────────
    op.create_table(
        "modernization_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("grade", sa.String(2), nullable=False),
        sa.Column("code_health", sa.Float, nullable=True),
        sa.Column("dependency_health", sa.Float, nullable=True),
        sa.Column("architecture_quality", sa.Float, nullable=True),
        sa.Column("test_coverage", sa.Float, nullable=True),
        sa.Column("documentation", sa.Float, nullable=True),
        sa.Column("infrastructure_readiness", sa.Float, nullable=True),
        sa.Column("security_posture", sa.Float, nullable=True),
        sa.Column("priority_areas", postgresql.JSONB, nullable=True),
    )
    op.create_index(
        "ix_modernization_scores_analysis_id",
        "modernization_scores",
        ["analysis_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("modernization_scores")
    op.drop_table("recommendations")
    op.drop_table("dependency_findings")
    op.drop_table("debt_items")
    op.drop_table("file_metrics")
    op.drop_table("analyses")
    op.drop_table("jobs")
    op.drop_table("projects")
    op.drop_table("users")
