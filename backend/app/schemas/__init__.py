"""
CodeLens AI — Pydantic Schemas Package.

Re-exports all request/response schemas used by the API layer.
"""

from app.schemas.common import (  # noqa: F401
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)
from app.schemas.user import UserCreate, UserResponse, UserSync  # noqa: F401
from app.schemas.project import (  # noqa: F401
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    ProjectUpdate,
)
from app.schemas.analysis import (  # noqa: F401
    AnalysisResponse,
    AnalysisSummaryResponse,
    FileMetricResponse,
    DebtItemResponse,
    DependencyFindingResponse,
    ScoreResponse,
    StructureResponse,
)
from app.schemas.job import JobResponse, JobStepResponse  # noqa: F401
from app.schemas.recommendation import (  # noqa: F401
    RecommendationResponse,
    RecommendationListResponse,
    RefactorRequest,
    RefactorResponse,
)
