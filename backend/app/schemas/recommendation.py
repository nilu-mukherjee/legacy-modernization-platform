"""
CodeLens AI — Recommendation Schemas.

Request/response schemas for AI-generated modernisation recommendations
and on-demand refactoring.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    """Full recommendation returned by the API."""

    id: uuid.UUID
    analysis_id: uuid.UUID
    category: str
    priority: int
    title: str
    description: str
    rationale: str | None = None
    implementation_steps: str | None = None
    estimated_hours: float | None = None
    impact_score: float | None = None
    affected_files: dict[str, Any] | None = None
    before_code: str | None = None
    after_code: str | None = None

    model_config = {"from_attributes": True}


class RecommendationListResponse(BaseModel):
    """Lightweight recommendation summary for list views."""

    id: uuid.UUID
    category: str
    priority: int
    title: str
    description: str
    estimated_hours: float | None = None
    impact_score: float | None = None

    model_config = {"from_attributes": True}


class RefactorRequest(BaseModel):
    """Request payload to generate a refactored code snippet via AI.

    The caller provides optional extra context or instructions that get
    appended to the AI prompt.
    """

    additional_context: str | None = Field(
        default=None,
        description="Optional extra instructions for the AI refactoring prompt.",
    )
    target_language: str | None = Field(
        default=None,
        description="Override the detected language (e.g. 'typescript').",
    )


class RefactorResponse(BaseModel):
    """Response containing the AI-generated refactored code."""

    recommendation_id: uuid.UUID
    original_code: str | None = None
    refactored_code: str
    explanation: str | None = None
    language: str | None = None
