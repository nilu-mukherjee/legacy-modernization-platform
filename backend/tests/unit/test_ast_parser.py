"""
Unit tests for app.services.ast_parser — multi-language AST parsing.

Tests use the regex fallback path so they run without tree-sitter grammars
installed, and are also valid when tree-sitter IS installed (same behaviour
is expected for well-formed inputs).
"""

from __future__ import annotations

import pytest

from app.services.ast_parser import ParseResult, _estimate_comment_ratio, parse_file


# ── Synthetic source fixtures ─────────────────────────────────────────────────

PYTHON_SIMPLE = '''\
def add(a, b):
    """Add two numbers."""
    return a + b


def no_doc(x):
    return x * 2
'''

PYTHON_COMPLEX = '''\
class DataProcessor:
    """Processes data records."""

    def process(self, records, config, logger, db, cache):
        """Process records."""
        result = []
        for record in records:
            if record.is_valid():
                if record.needs_transform():
                    if config.transform_enabled:
                        if record.type == "A":
                            if record.subtype == "A1":
                                result.append(record.transform())
        return result

    def helper(self):
        pass
'''

PYTHON_IMPORTS = """\
import os
import sys
from pathlib import Path

x = 1
"""

PYTHON_COMMENTS = """\
# Module comment
# Another comment
def foo():
    # inline comment
    return 1
x = 2
"""

JS_SIMPLE = """\
function greet(name) {
    return `Hello, ${name}`;
}

const double = (x) => x * 2;
"""

JS_CLASS = """\
class Animal {
    constructor(name) {
        this.name = name;
    }

    speak() {
        console.log(this.name + ' makes a noise.');
    }

    toString() {
        return `Animal(${this.name})`;
    }
}
"""

JAVA_SIMPLE = """\
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    private int subtract(int a, int b) {
        return a - b;
    }
}
"""


# ── ParseResult shape ─────────────────────────────────────────────────────────


class TestParseResult:
    def test_returns_parse_result(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert isinstance(result, ParseResult)

    def test_file_metrics_present(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert result.file_metrics is not None

    def test_functions_list_present(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert isinstance(result.functions, list)

    def test_classes_list_present(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert isinstance(result.classes, list)

    def test_empty_content_does_not_crash(self) -> None:
        result = parse_file("src/empty.py", "", "python")
        assert isinstance(result, ParseResult)
        assert result.file_metrics.loc == 0

    def test_unknown_language_does_not_crash(self) -> None:
        result = parse_file("src/file.cobol", "IDENTIFICATION DIVISION.", "cobol")
        assert isinstance(result, ParseResult)


# ── Python — file metrics ─────────────────────────────────────────────────────


class TestPythonFileMetrics:
    def test_loc_counted_correctly(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert result.file_metrics.loc == len(PYTHON_SIMPLE.splitlines())

    def test_function_count(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert result.file_metrics.function_count == 2

    def test_class_count(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        assert result.file_metrics.class_count >= 1

    def test_import_count(self) -> None:
        result = parse_file("src/utils.py", PYTHON_IMPORTS, "python")
        assert result.file_metrics.import_count >= 3

    def test_language_stored(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        assert result.file_metrics.language == "python"

    def test_language_normalised_to_lower(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "Python")
        assert result.file_metrics.language == "python"

    def test_all_metric_fields_non_negative(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        fm = result.file_metrics
        assert fm.loc >= 0
        assert fm.function_count >= 0
        assert fm.class_count >= 0
        assert fm.import_count >= 0
        assert fm.max_complexity >= 0
        assert fm.max_nesting >= 0
        assert 0.0 <= fm.comment_ratio <= 1.0


# ── Python — function metrics ─────────────────────────────────────────────────


class TestPythonFunctionMetrics:
    def test_function_names_extracted(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        names = {f.name for f in result.functions}
        assert "add" in names
        assert "no_doc" in names

    def test_has_docstring_true(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        add_fn = next((f for f in result.functions if f.name == "add"), None)
        assert add_fn is not None
        assert add_fn.has_docstring is True

    def test_has_docstring_false(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        no_doc_fn = next((f for f in result.functions if f.name == "no_doc"), None)
        assert no_doc_fn is not None
        assert no_doc_fn.has_docstring is False

    def test_param_count_excludes_self(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        process_fn = next((f for f in result.functions if f.name == "process"), None)
        assert process_fn is not None
        # def process(self, records, config, logger, db, cache) → 5 real params
        assert process_fn.param_count == 5

    def test_complex_function_complexity_above_one(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        process_fn = next((f for f in result.functions if f.name == "process"), None)
        assert process_fn is not None
        assert process_fn.complexity > 1

    def test_file_path_on_function_metrics(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        for fn in result.functions:
            assert fn.file_path == "src/utils.py"

    def test_function_loc_positive(self) -> None:
        result = parse_file("src/utils.py", PYTHON_SIMPLE, "python")
        for fn in result.functions:
            assert fn.loc > 0


# ── Python — class metrics ────────────────────────────────────────────────────


class TestPythonClassMetrics:
    def test_class_name_extracted(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        assert result.classes
        assert result.classes[0].name == "DataProcessor"

    def test_class_method_count(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        assert result.classes
        # DataProcessor has process + helper = 2 methods
        assert result.classes[0].method_count >= 2

    def test_class_loc_positive(self) -> None:
        result = parse_file("src/processor.py", PYTHON_COMPLEX, "python")
        assert result.classes
        assert result.classes[0].loc > 0


# ── JavaScript parsing ────────────────────────────────────────────────────────


class TestJavaScriptParsing:
    def test_function_detected(self) -> None:
        result = parse_file("src/utils.js", JS_SIMPLE, "javascript")
        assert result.file_metrics.function_count >= 1

    def test_class_detected(self) -> None:
        result = parse_file("src/animal.js", JS_CLASS, "javascript")
        assert result.file_metrics.class_count >= 1

    def test_class_name(self) -> None:
        result = parse_file("src/animal.js", JS_CLASS, "javascript")
        if result.classes:
            assert result.classes[0].name == "Animal"

    def test_loc_correct(self) -> None:
        result = parse_file("src/utils.js", JS_SIMPLE, "javascript")
        assert result.file_metrics.loc == len(JS_SIMPLE.splitlines())

    def test_typescript_does_not_crash(self) -> None:
        ts = "function identity<T>(value: T): T { return value; }\n"
        result = parse_file("src/id.ts", ts, "typescript")
        assert isinstance(result, ParseResult)

    def test_tsx_does_not_crash(self) -> None:
        tsx = "const App = () => <div>Hello</div>;\n"
        result = parse_file("src/App.tsx", tsx, "tsx")
        assert isinstance(result, ParseResult)


# ── Java parsing ──────────────────────────────────────────────────────────────


class TestJavaParsing:
    def test_methods_detected(self) -> None:
        result = parse_file("src/Calculator.java", JAVA_SIMPLE, "java")
        assert result.file_metrics.function_count >= 2

    def test_class_detected(self) -> None:
        result = parse_file("src/Calculator.java", JAVA_SIMPLE, "java")
        assert result.file_metrics.class_count >= 1

    def test_loc_correct(self) -> None:
        result = parse_file("src/Calculator.java", JAVA_SIMPLE, "java")
        assert result.file_metrics.loc == len(JAVA_SIMPLE.splitlines())


# ── Comment ratio ─────────────────────────────────────────────────────────────


class TestCommentRatio:
    def test_no_comments_returns_zero(self) -> None:
        content = "x = 1\ny = 2\nz = x + y\n"
        assert _estimate_comment_ratio(content, "python") == 0.0

    def test_all_comments_returns_one(self) -> None:
        content = "# line1\n# line2\n# line3\n"
        assert _estimate_comment_ratio(content, "python") == 1.0

    def test_mixed_returns_partial(self) -> None:
        ratio = _estimate_comment_ratio(PYTHON_COMMENTS, "python")
        assert 0.0 < ratio < 1.0

    def test_empty_content_returns_zero(self) -> None:
        assert _estimate_comment_ratio("", "python") == 0.0

    def test_js_line_comments_detected(self) -> None:
        content = "// comment\nconst x = 1;\n// another\n"
        ratio = _estimate_comment_ratio(content, "javascript")
        assert ratio > 0.0

    def test_ratio_never_exceeds_one(self) -> None:
        content = "# a\n# b\n# c\nx = 1\n"
        ratio = _estimate_comment_ratio(content, "python")
        assert ratio <= 1.0
