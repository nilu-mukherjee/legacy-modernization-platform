"""
Unit tests for app.services.debt_detector — rule-based debt detection.
"""

from __future__ import annotations

import pytest

from app.services.debt_detector import (
    ClassMetrics,
    DebtFinding,
    FileMetrics,
    FunctionMetrics,
    detect_class_debt,
    detect_file_debt,
    detect_function_debt,
    detect_security_issues,
)


class TestFunctionDebt:
    def test_clean_function_no_findings(self) -> None:
        func = FunctionMetrics(
            name="clean_fn",
            file_path="src/utils.py",
            loc=20,
            complexity=3,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        assert detect_function_debt(func) == []

    def test_critical_complexity_detected(self) -> None:
        func = FunctionMetrics(
            name="monster_fn",
            file_path="src/legacy.py",
            loc=30,
            complexity=25,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "COMPLEXITY_CRITICAL" in rule_ids

    def test_high_complexity_not_critical(self) -> None:
        func = FunctionMetrics(
            name="complex_fn",
            file_path="src/legacy.py",
            loc=30,
            complexity=15,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "COMPLEXITY_HIGH" in rule_ids
        assert "COMPLEXITY_CRITICAL" not in rule_ids

    def test_very_long_function_detected(self) -> None:
        func = FunctionMetrics(
            name="huge_fn",
            file_path="src/legacy.py",
            loc=200,
            complexity=5,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "VERY_LONG_FUNCTION" in rule_ids

    def test_long_function_not_very_long(self) -> None:
        func = FunctionMetrics(
            name="long_fn",
            file_path="src/legacy.py",
            loc=80,
            complexity=5,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "LONG_FUNCTION" in rule_ids
        assert "VERY_LONG_FUNCTION" not in rule_ids

    def test_deep_nesting_detected(self) -> None:
        func = FunctionMetrics(
            name="nested_fn",
            file_path="src/legacy.py",
            loc=30,
            complexity=5,
            nesting_depth=6,
            param_count=2,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "DEEP_NESTING" in rule_ids

    def test_too_many_params_detected(self) -> None:
        func = FunctionMetrics(
            name="param_heavy",
            file_path="src/legacy.py",
            loc=30,
            complexity=5,
            nesting_depth=2,
            param_count=7,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "TOO_MANY_PARAMS" in rule_ids

    def test_exactly_5_params_not_flagged(self) -> None:
        func = FunctionMetrics(
            name="ok_fn",
            file_path="src/utils.py",
            loc=20,
            complexity=3,
            nesting_depth=2,
            param_count=5,
            has_docstring=True,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "TOO_MANY_PARAMS" not in rule_ids

    def test_missing_docstring_flagged_for_nontrivial(self) -> None:
        func = FunctionMetrics(
            name="undocumented",
            file_path="src/utils.py",
            loc=20,
            complexity=3,
            nesting_depth=2,
            param_count=2,
            has_docstring=False,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "NO_DOCSTRING" in rule_ids

    def test_missing_docstring_not_flagged_for_trivial(self) -> None:
        func = FunctionMetrics(
            name="trivial",
            file_path="src/utils.py",
            loc=5,
            complexity=1,
            nesting_depth=0,
            param_count=1,
            has_docstring=False,
        )
        rule_ids = [f.rule_id for f in detect_function_debt(func)]
        assert "NO_DOCSTRING" not in rule_ids

    def test_finding_has_required_fields(self) -> None:
        func = FunctionMetrics(
            name="complex_fn",
            file_path="src/legacy.py",
            loc=30,
            complexity=25,
            nesting_depth=2,
            param_count=2,
            has_docstring=True,
        )
        findings = detect_function_debt(func)
        assert findings
        f = findings[0]
        assert isinstance(f, DebtFinding)
        assert f.rule_id
        assert f.category
        assert f.severity in ("low", "medium", "high", "critical")
        assert f.title
        assert f.file_path == "src/legacy.py"
        assert f.estimated_hours >= 0.0


class TestClassDebt:
    def test_normal_class_no_findings(self) -> None:
        cls = ClassMetrics(name="UserService", file_path="src/services.py", method_count=10)
        assert detect_class_debt(cls) == []

    def test_god_class_detected(self) -> None:
        cls = ClassMetrics(name="GodObject", file_path="src/legacy.py", method_count=25)
        rule_ids = [f.rule_id for f in detect_class_debt(cls)]
        assert "GOD_CLASS" in rule_ids

    def test_exactly_20_methods_not_flagged(self) -> None:
        cls = ClassMetrics(name="BigClass", file_path="src/legacy.py", method_count=20)
        assert detect_class_debt(cls) == []

    def test_21_methods_flagged(self) -> None:
        cls = ClassMetrics(name="GodClass", file_path="src/legacy.py", method_count=21)
        assert any(f.rule_id == "GOD_CLASS" for f in detect_class_debt(cls))

    def test_god_class_severity_is_high(self) -> None:
        cls = ClassMetrics(name="GodClass", file_path="src/legacy.py", method_count=30)
        findings = detect_class_debt(cls)
        god = next(f for f in findings if f.rule_id == "GOD_CLASS")
        assert god.severity == "high"


class TestFileDebt:
    def test_normal_file_no_findings(self) -> None:
        fm = FileMetrics(file_path="src/utils.py", language="python", loc=200)
        assert detect_file_debt(fm) == []

    def test_large_file_detected(self) -> None:
        fm = FileMetrics(file_path="src/legacy.py", language="python", loc=600)
        rule_ids = [f.rule_id for f in detect_file_debt(fm)]
        assert "LARGE_FILE" in rule_ids

    def test_exactly_500_loc_not_flagged(self) -> None:
        fm = FileMetrics(file_path="src/utils.py", language="python", loc=500)
        assert detect_file_debt(fm) == []

    def test_501_loc_flagged(self) -> None:
        fm = FileMetrics(file_path="src/big.py", language="python", loc=501)
        assert any(f.rule_id == "LARGE_FILE" for f in detect_file_debt(fm))


class TestSecurityIssues:
    def test_clean_file_no_findings(self) -> None:
        content = "def hello():\n    return 'world'\n"
        assert detect_security_issues("src/utils.py", content) == []

    def test_hardcoded_api_key_detected(self) -> None:
        content = 'api_key = "sk-abcdefghij1234567890"\n'
        findings = detect_security_issues("src/config.py", content)
        assert any(f.rule_id == "HARDCODED_SECRET" for f in findings)

    def test_aws_key_pattern_detected(self) -> None:
        content = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\n"
        findings = detect_security_issues("src/aws.py", content)
        assert any(f.rule_id == "HARDCODED_SECRET" for f in findings)

    def test_github_pat_detected(self) -> None:
        content = "token = 'ghp_" + "a" * 36 + "'\n"
        findings = detect_security_issues("src/client.py", content)
        assert any(f.rule_id == "HARDCODED_SECRET" for f in findings)

    def test_eval_usage_detected(self) -> None:
        content = "result = eval(user_input)\n"
        findings = detect_security_issues("src/processor.py", content)
        assert any("eval" in f.title.lower() for f in findings)

    def test_exec_usage_detected(self) -> None:
        content = "exec(compile(source, '<string>', 'exec'))\n"
        findings = detect_security_issues("src/runner.py", content)
        assert any("exec" in f.title.lower() for f in findings)

    def test_sql_injection_concat_detected(self) -> None:
        content = 'cursor.execute("SELECT * FROM users WHERE id = " + user_id)\n'
        findings = detect_security_issues("src/db.py", content)
        assert any(f.severity in ("high", "critical") for f in findings)

    def test_finding_includes_line_number(self) -> None:
        content = "x = 1\napi_key = 'ghp_" + "b" * 36 + "'\n"
        findings = detect_security_issues("src/config.py", content)
        secret_findings = [f for f in findings if f.rule_id == "HARDCODED_SECRET"]
        assert secret_findings
        assert secret_findings[0].line_start == 2

    def test_empty_file_no_findings(self) -> None:
        assert detect_security_issues("src/empty.py", "") == []

    def test_findings_have_suggestions(self) -> None:
        content = "result = eval(user_input)\n"
        findings = detect_security_issues("src/processor.py", content)
        for f in findings:
            assert f.suggestion
