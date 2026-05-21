"""
Common Schemas
==============

Reusable base classes and generic response wrappers shared across all
endpoint schemas.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Standard success response wrapper."""

    message: str = "Success"


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
    status_code: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T]
    total: int
    skip: int = 0
    limit: int = 20


class HealthResponse(BaseModel):
    """Response for the ``/health`` endpoint."""

    status: str = "healthy"
    version: str
    database: str = "connected"
    redis: str = "connected"


class OrmBase(BaseModel):
    """
    Base class for schemas that are read from SQLAlchemy ORM models.

    Enables ``model_validate(orm_obj)`` by setting ``from_attributes = True``.
    """

    model_config = ConfigDict(from_attributes=True)
