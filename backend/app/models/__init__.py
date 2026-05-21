"""
ORM Models Package
==================

Imports every model so that ``Base.metadata`` knows about all tables when
Alembic runs ``--autogenerate``.
"""

from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.analysis import Analysis, FileMetric, DebtItem, DependencyFinding  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.score import ModernizationScore  # noqa: F401
from app.models.job import Job  # noqa: F401

__all__ = [
    "User",
    "Project",
    "Analysis",
    "FileMetric",
    "DebtItem",
    "DependencyFinding",
    "Recommendation",
    "ModernizationScore",
    "Job",
]
