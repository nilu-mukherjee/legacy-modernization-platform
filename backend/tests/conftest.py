"""
Shared pytest fixtures for the CodeLens AI backend test suite.
"""

from __future__ import annotations

import pytest

from app.services.scoring import AnalysisMetrics


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
