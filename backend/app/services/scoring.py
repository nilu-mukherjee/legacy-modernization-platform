"""
Modernization Scoring Service
==============================

Calculates a composite **Modernization Readiness Score** (0-100) across seven
weighted dimensions.  The score is the headline number shown on the dashboard
and drives the grade (A – F).

Dimensions & weights:
    code_health            25 %
    dependency_health      20 %
    architecture_quality   15 %
    test_coverage          15 %
    documentation          10 %
    infrastructure_ready.  10 %
    security_posture        5 %
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Weights ──────────────────────────────────────────────────────────────────

WEIGHTS: dict[str, float] = {
    "code_health": 0.25,
    "dependency_health": 0.20,
    "architecture_quality": 0.15,
    "test_coverage": 0.15,
    "documentation": 0.10,
    "infrastructure_readiness": 0.10,
    "security_posture": 0.05,
}


# ── Input Dataclass ──────────────────────────────────────────────────────────


@dataclass
class AnalysisMetrics:
    """
    Aggregated metrics fed into the scoring algorithm.

    Populated by the metrics-computation stage of the pipeline.
    """

    # Code health inputs
    avg_cyclomatic_complexity: float = 0.0
    long_methods: int = 0       # Functions > 60 LOC.
    total_methods: int = 0
    large_files: int = 0        # Files > 500 LOC.
    total_files: int = 0

    # Dependency health inputs
    outdated_deps: int = 0
    total_deps: int = 0
    vulnerability_count: int = 0
    deprecated_deps: int = 0

    # Architecture quality inputs
    avg_imports_per_file: float = 0.0
    circular_dependencies: int = 0

    # Test coverage inputs
    test_file_count: int = 0
    source_file_count: int = 0
    has_test_config: bool = False

    # Documentation inputs
    has_readme: bool = False
    readme_loc: int = 0
    overall_comment_ratio: float = 0.0

    # Infrastructure inputs
    has_dockerfile: bool = False
    has_ci_config: bool = False
    has_env_example: bool = False
    has_linter_config: bool = False

    # Security inputs
    potential_secrets_count: int = 0
    security_vulnerability_count: int = 0


# ── Output Dataclass ─────────────────────────────────────────────────────────


@dataclass
class ScoreResult:
    """Final scoring output written to the ``modernization_scores`` table."""

    overall_score: float
    grade: str
    code_health: float
    dependency_health: float
    architecture_quality: float
    test_coverage: float
    documentation: float
    infrastructure_readiness: float
    security_posture: float
    priority_areas: list[dict] = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _clamp(lo: float, hi: float, value: float) -> float:
    """Clamp *value* to the range [lo, hi]."""
    return max(lo, min(hi, value))


def _grade(score: float) -> str:
    """Map a 0-100 score to a letter grade."""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


# ── Main Scoring Function ───────────────────────────────────────────────────


def calculate_modernization_score(metrics: AnalysisMetrics) -> ScoreResult:
    """
    Compute the composite modernization readiness score.

    Each dimension is scored independently on a 0-100 scale, then combined
    via the weight table above.

    Args:
        metrics: Aggregated analysis metrics.

    Returns:
        A :class:`ScoreResult` with the overall score, grade, sub-scores,
        and the top-3 priority areas for improvement.
    """

    # ── Code Health (25%) ────────────────────────────────────────────────
    long_ratio = metrics.long_methods / max(metrics.total_methods, 1)
    large_ratio = metrics.large_files / max(metrics.total_files, 1)
    code_health = _clamp(
        0,
        100,
        100
        - (metrics.avg_cyclomatic_complexity * 5)
        - (long_ratio * 50)
        - (large_ratio * 30),
    )

    # ── Dependency Health (20%) ──────────────────────────────────────────
    outdated_ratio = metrics.outdated_deps / max(metrics.total_deps, 1)
    dependency_health = _clamp(
        0,
        100,
        100
        - (outdated_ratio * 60)
        - (metrics.vulnerability_count * 8)
        - (metrics.deprecated_deps * 15),
    )

    # ── Architecture Quality (15%) ───────────────────────────────────────
    architecture_quality = _clamp(
        0,
        100,
        100
        - (max(0, metrics.avg_imports_per_file - 5) * 5)
        - (metrics.circular_dependencies * 20),
    )

    # ── Test Coverage (15%) ──────────────────────────────────────────────
    has_tests = metrics.test_file_count > 0
    test_ratio = metrics.test_file_count / max(metrics.source_file_count, 1)
    test_coverage = _clamp(
        0,
        100,
        (min(100, test_ratio * 200) if has_tests else 0)
        + (10 if metrics.has_test_config else 0),
    )

    # ── Documentation (10%) ──────────────────────────────────────────────
    readme_quality = min(1.0, metrics.readme_loc / 50)
    documentation = _clamp(
        0,
        100,
        (40 if metrics.has_readme else 0)
        + (min(30, readme_quality * 30))
        + (min(30, metrics.overall_comment_ratio * 300)),
    )

    # ── Infrastructure Readiness (10%) ───────────────────────────────────
    infrastructure_readiness = float(
        (30 if metrics.has_dockerfile else 0)
        + (30 if metrics.has_ci_config else 0)
        + (20 if metrics.has_env_example else 0)
        + (20 if metrics.has_linter_config else 0)
    )

    # ── Security Posture (5%) ────────────────────────────────────────────
    security_posture = _clamp(
        0,
        100,
        100
        - (metrics.potential_secrets_count * 25)
        - (metrics.security_vulnerability_count * 15),
    )

    # ── Weighted Composite ───────────────────────────────────────────────
    sub_scores = {
        "code_health": round(code_health, 1),
        "dependency_health": round(dependency_health, 1),
        "architecture_quality": round(architecture_quality, 1),
        "test_coverage": round(test_coverage, 1),
        "documentation": round(documentation, 1),
        "infrastructure_readiness": round(infrastructure_readiness, 1),
        "security_posture": round(security_posture, 1),
    }

    overall = sum(sub_scores[k] * WEIGHTS[k] for k in WEIGHTS)

    # Identify the three lowest-scoring areas as priorities.
    priority_areas = sorted(
        [{"area": k, "score": v} for k, v in sub_scores.items()],
        key=lambda x: x["score"],
    )[:3]

    return ScoreResult(
        overall_score=round(overall, 1),
        grade=_grade(overall),
        code_health=sub_scores["code_health"],
        dependency_health=sub_scores["dependency_health"],
        architecture_quality=sub_scores["architecture_quality"],
        test_coverage=sub_scores["test_coverage"],
        documentation=sub_scores["documentation"],
        infrastructure_readiness=sub_scores["infrastructure_readiness"],
        security_posture=sub_scores["security_posture"],
        priority_areas=priority_areas,
    )
