"""
Unit tests for app.services.scoring — modernization score calculation.
"""

from __future__ import annotations

import pytest

from app.services.scoring import AnalysisMetrics, ScoreResult, calculate_modernization_score, _grade, WEIGHTS


class TestGrading:
    def test_grade_a_at_80(self) -> None:
        metrics = AnalysisMetrics(
            has_readme=True,
            readme_loc=100,
            has_dockerfile=True,
            has_ci_config=True,
            has_env_example=True,
            has_linter_config=True,
            has_test_config=True,
            total_files=10,
            source_file_count=10,
            test_file_count=5,
            total_deps=5,
            overall_comment_ratio=0.15,
        )
        result = calculate_modernization_score(metrics)
        assert result.grade == "A"
        assert result.overall_score >= 80

    def test_grade_f_for_legacy(self, legacy_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(legacy_metrics)
        assert result.grade in ("D", "F")
        assert result.overall_score < 40

    @pytest.mark.parametrize(
        "score,expected",
        [
            (80.0, "A"),
            (79.9, "B"),
            (60.0, "B"),
            (59.9, "C"),
            (40.0, "C"),
            (39.9, "D"),
            (20.0, "D"),
            (19.9, "F"),
            (0.0, "F"),
            (100.0, "A"),
        ],
    )
    def test_grade_boundaries(self, score: float, expected: str) -> None:
        assert _grade(score) == expected


class TestSubScores:
    def test_returns_score_result(self, minimal_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(minimal_metrics)
        assert isinstance(result, ScoreResult)

    def test_all_sub_scores_in_range(self, minimal_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(minimal_metrics)
        for value in (
            result.code_health,
            result.dependency_health,
            result.architecture_quality,
            result.test_coverage,
            result.documentation,
            result.infrastructure_readiness,
            result.security_posture,
        ):
            assert 0.0 <= value <= 100.0

    def test_overall_score_in_range(self, minimal_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(minimal_metrics)
        assert 0.0 <= result.overall_score <= 100.0

    def test_priority_areas_three_lowest(self, legacy_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(legacy_metrics)
        assert len(result.priority_areas) == 3
        scores = [p["score"] for p in result.priority_areas]
        assert scores == sorted(scores)

    def test_priority_areas_have_area_and_score_keys(self, minimal_metrics: AnalysisMetrics) -> None:
        result = calculate_modernization_score(minimal_metrics)
        for item in result.priority_areas:
            assert "area" in item
            assert "score" in item

    def test_no_deps_does_not_crash(self) -> None:
        result = calculate_modernization_score(AnalysisMetrics(total_deps=0, outdated_deps=0))
        assert result.dependency_health == 100.0

    def test_no_methods_does_not_crash(self) -> None:
        result = calculate_modernization_score(AnalysisMetrics(total_methods=0, long_methods=0))
        assert result.code_health >= 0.0

    def test_empty_metrics_produces_valid_result(self) -> None:
        result = calculate_modernization_score(AnalysisMetrics())
        assert isinstance(result, ScoreResult)
        assert 0.0 <= result.overall_score <= 100.0


class TestInfrastructureScore:
    def test_full_infra_scores_100(self) -> None:
        metrics = AnalysisMetrics(
            has_dockerfile=True,
            has_ci_config=True,
            has_env_example=True,
            has_linter_config=True,
        )
        result = calculate_modernization_score(metrics)
        assert result.infrastructure_readiness == 100.0

    def test_no_infra_scores_0(self) -> None:
        metrics = AnalysisMetrics(
            has_dockerfile=False,
            has_ci_config=False,
            has_env_example=False,
            has_linter_config=False,
        )
        result = calculate_modernization_score(metrics)
        assert result.infrastructure_readiness == 0.0

    def test_partial_infra_between_0_and_100(self) -> None:
        metrics = AnalysisMetrics(has_dockerfile=True, has_ci_config=False)
        result = calculate_modernization_score(metrics)
        assert 0.0 < result.infrastructure_readiness < 100.0


class TestSecurityScore:
    def test_clean_scores_100(self) -> None:
        result = calculate_modernization_score(
            AnalysisMetrics(potential_secrets_count=0, security_vulnerability_count=0)
        )
        assert result.security_posture == 100.0

    def test_secrets_reduce_score(self) -> None:
        clean = calculate_modernization_score(AnalysisMetrics(potential_secrets_count=0))
        dirty = calculate_modernization_score(AnalysisMetrics(potential_secrets_count=3))
        assert dirty.security_posture < clean.security_posture

    def test_security_score_clamps_to_zero(self) -> None:
        result = calculate_modernization_score(
            AnalysisMetrics(potential_secrets_count=10, security_vulnerability_count=10)
        )
        assert result.security_posture == 0.0


class TestWeights:
    def test_weights_sum_to_one(self) -> None:
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_code_health_is_highest_weight(self) -> None:
        assert WEIGHTS["code_health"] == max(WEIGHTS.values())

    def test_security_posture_is_lowest_weight(self) -> None:
        assert WEIGHTS["security_posture"] == min(WEIGHTS.values())

    def test_all_seven_dimensions_present(self) -> None:
        expected = {
            "code_health",
            "dependency_health",
            "architecture_quality",
            "test_coverage",
            "documentation",
            "infrastructure_readiness",
            "security_posture",
        }
        assert set(WEIGHTS.keys()) == expected


class TestTestCoverageScore:
    def test_no_tests_scores_zero(self) -> None:
        result = calculate_modernization_score(
            AnalysisMetrics(test_file_count=0, source_file_count=10, has_test_config=False)
        )
        assert result.test_coverage == 0.0

    def test_equal_test_and_source_files_scores_high(self) -> None:
        result = calculate_modernization_score(
            AnalysisMetrics(test_file_count=10, source_file_count=10, has_test_config=True)
        )
        assert result.test_coverage == 100.0

    def test_test_config_adds_points(self) -> None:
        without = calculate_modernization_score(
            AnalysisMetrics(test_file_count=1, source_file_count=10, has_test_config=False)
        )
        with_config = calculate_modernization_score(
            AnalysisMetrics(test_file_count=1, source_file_count=10, has_test_config=True)
        )
        assert with_config.test_coverage > without.test_coverage
