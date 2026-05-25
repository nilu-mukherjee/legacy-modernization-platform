"""
Recommendation Schemas
======================

Request / response models for AI-generated recommendations and on-demand
refactoring.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import OrmBase


class RecommendationResponse(OrmBase):
    """A single AI recommendation."""

    id: UUID
    category: str
    priority: str
    title: str
    description: Optional[str]
    rationale: Optional[str]
    implementation_steps: Optional[str]
    estimated_hours: Optional[float]
    impact_score: Optional[float]
    affected_files: Optional[list]
    before_code: Optional[str]
    after_code: Optional[str]


class RecommendationListResponse(BaseModel):
    """All recommendations with summary counts."""

    recommendations: list[RecommendationResponse]
    total: int
    by_priority: dict


class RefactorRequest(BaseModel):
    """Optional context for on-demand refactoring."""

    file_path: Optional[str] = None
    file_content: Optional[str] = None
    language: Optional[str] = None
    additional_context: Optional[str] = None


class RefactorResponse(BaseModel):
    """AI-generated refactored code."""

    recommendation_id: UUID
    file_path: Optional[str]
    language: Optional[str]
    before_code: Optional[str]
    after_code: str
    explanation: str
