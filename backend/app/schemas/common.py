"""
CodeLens AI — Common Pydantic Schemas.

Shared response envelopes and utility schemas used across all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Standard envelope for single-resource API responses.

    All successful responses are wrapped in this structure so the frontend
    has a consistent shape to parse.
    """

    success: bool = True
    data: T
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope for paginated list responses.

    Includes item count and pagination metadata alongside the result list.
    """

    success: bool = True
    data: list[T]
    total: int = Field(description="Total number of records matching the query.")
    page: int = Field(default=1, description="Current page number (1-indexed).")
    page_size: int = Field(default=20, description="Number of records per page.")
    has_more: bool = Field(default=False, description="Whether more pages exist.")


class ErrorResponse(BaseModel):
    """Standard error response returned for 4xx/5xx status codes."""

    success: bool = False
    error: str = Field(description="Machine-readable error code or type.")
    detail: str = Field(description="Human-readable error message.")
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional list of field-level validation errors.",
    )


class HealthResponse(BaseModel):
    """Response payload for the ``/health`` endpoint."""

    status: str = "ok"
    app_name: str
    version: str
    environment: str
    timestamp: datetime
