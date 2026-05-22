"""
Shared pytest fixtures for the CodeLens AI backend test suite.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.user import User
from app.services.scoring import AnalysisMetrics


# ── Scoring fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def minimal_metrics() -> AnalysisMetrics:
    """Bare-minimum AnalysisMetrics with all defaults (should score high)."""
    return AnalysisMetrics(
        has_readme=True,
        has_dockerfile=True,
        has_ci_config=True,
        has_env_example=True,
        has_linter_config=True,
        has_test_config=True,
        total_files=10,
        source_file_count=10,
        test_file_count=3,
    )


@pytest.fixture()
def legacy_metrics() -> AnalysisMetrics:
    """Metrics representing a heavily debt-laden legacy codebase."""
    return AnalysisMetrics(
        avg_cyclomatic_complexity=15.0,
        long_methods=20,
        total_methods=25,
        large_files=8,
        total_files=10,
        outdated_deps=15,
        total_deps=20,
        vulnerability_count=5,
        deprecated_deps=3,
        test_file_count=0,
        source_file_count=10,
        has_readme=False,
        has_dockerfile=False,
        has_ci_config=False,
        has_env_example=False,
        has_linter_config=False,
        potential_secrets_count=2,
        security_vulnerability_count=3,
    )


# ── API integration fixtures ──────────────────────────────────────────────────


@pytest.fixture()
def mock_user() -> User:
    """A synthetic User instance for use in dependency overrides."""
    user = User.__new__(User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.avatar_url = None
    user.github_id = "99999"
    user.github_access_token = None
    return user


@pytest.fixture()
async def http_client(mock_user: User) -> AsyncClient:
    """
    AsyncClient wired to the FastAPI app with all external I/O stubbed:
    - Redis / ARQ pool initialisation (lifespan) mocked out
    - ``get_current_user`` overridden to return ``mock_user``
    - ``get_db`` overridden with an AsyncMock session
    - ``get_arq_pool`` overridden with an AsyncMock pool
    """
    from app.core.database import get_db
    from app.core.redis import get_arq_pool
    from app.core.security import get_current_user
    from app.main import app

    mock_db = AsyncMock()
    mock_arq = AsyncMock()

    # Make scalar()/scalar_one_or_none()/scalars().all() return sensible defaults.
    mock_execute = AsyncMock()
    mock_execute.scalar.return_value = 0
    mock_execute.scalar_one_or_none.return_value = None
    mock_execute.scalars.return_value.all.return_value = []
    mock_execute.all.return_value = []
    mock_db.execute.return_value = mock_execute

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_arq_pool] = lambda: mock_arq

    # Patch Redis/ARQ init so the lifespan does not attempt real connections.
    with (
        patch("app.main.init_redis", new_callable=AsyncMock),
        patch("app.main.init_arq", new_callable=AsyncMock),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.close_arq", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture()
async def unauthenticated_client() -> AsyncClient:
    """AsyncClient with no auth override — exercises the real 401 guard."""
    from app.main import app

    with (
        patch("app.main.init_redis", new_callable=AsyncMock),
        patch("app.main.init_arq", new_callable=AsyncMock),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.close_arq", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
