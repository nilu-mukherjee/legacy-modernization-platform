"""
AST Parser Service
==================

Multi-language AST analysis using tree-sitter. Extracts function / class
metrics, cyclomatic complexity, and nesting depth.

Supported languages: Python, JavaScript, TypeScript, Java.

Falls back to regex-based analysis when tree-sitter grammars are not
available so the pipeline keeps running in environments that haven't
installed the native grammar packages.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

from app.services.debt_detector import ClassMetrics, FileMetrics, FunctionMetrics

# ── Optional tree-sitter imports ─────────────────────────────────────────────

try:
    from tree_sitter import Language, Parser  # type: ignore[import]

    _TS_AVAILABLE = True
except ImportError:
    _TS_AVAILABLE = False

# Language singletons — populated lazily on first use.
_LANGUAGES: dict[str, Any] = {}


def _get_language(lang: str) -> Any | None:
    """Return the tree-sitter Language for *lang*, or None if unavailable."""
    if not _TS_AVAILABLE:
        return None
    if lang in _LANGUAGES:
        return _LANGUAGES[lang]

    language_obj: Any = None
    try:
        if lang == "python":
            import tree_sitter_python as m  # type: ignore[import]
            language_obj = Language(m.language())
        elif lang in ("javascript", "jsx"):
            import tree_sitter_javascript as m  # type: ignore[import]
            language_obj = Language(m.language())
        elif lang == "typescript":
            import tree_sitter_typescript as m  # type: ignore[import]
            language_obj = Language(m.language_typescript())
        elif lang == "tsx":
            import tree_sitter_typescript as m  # type: ignore[import]
            language_obj = Language(m.language_tsx())
        elif lang == "java":
            import tree_sitter_java as m  # type: ignore[import]
            language_obj = Language(m.language())
    except (ImportError, Exception):
        language_obj = None

    _LANGUAGES[lang] = language_obj
    return language_obj


# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class ParseResult:
    """Structured output from parsing a single source file."""

    file_metrics: FileMetrics
    functions: list[FunctionMetrics] = field(default_factory=list)
    classes: list[ClassMetrics] = field(default_factory=list)


# ── Public API ────────────────────────────────────────────────────────────────


def parse_file(file_path: str, content: str, language: str) -> ParseResult:
    """
    Parse *content* of a source file and return structural metrics.

    Tries tree-sitter first; falls back to regex heuristics if the grammar
    package is not installed.

    Args:
        file_path: Relative path of the file (used for metric labels).
        content: Full source text.
        language: Normalised language string (e.g. ``"python"``).

    Returns:
        A :class:`ParseResult` with aggregate file metrics plus per-function
        and per-class details.
    """
    lang = language.lower()
    ts_language = _get_language(lang)

    if ts_language is not None and _TS_AVAILABLE:
        try:
            return _parse_with_tree_sitter(file_path, content, lang, ts_language)
        except Exception as exc:
            logger.warning("tree-sitter parse failed for %s, falling back to regex: %s", file_path, exc)

    return _parse_with_regex(file_path, content, lang)


# ── tree-sitter implementation ────────────────────────────────────────────────

# Node type names that represent a new block scope (for nesting depth).
_BLOCK_TYPES: set[str] = {
    "block",
    "if_statement",
    "for_statement",
    "for_in_statement",
    "for_of_statement",
    "while_statement",
    "do_statement",
    "try_statement",
    "catch_clause",
    "with_statement",
    "switch_statement",
    "switch_body",
    "compound_statement",
}

# Node type names that add +1 to cyclomatic complexity.
_COMPLEXITY_NODES: set[str] = {
    "if_statement",
    "elif_clause",
    "else_if_clause",
    "for_statement",
    "for_in_statement",
    "for_of_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "catch_clause",
    "except_clause",
    "with_statement",
    "case_clause",
    "switch_case",
    "conditional_expression",
    "ternary_expression",
    "boolean_operator",
    "logical_expression",
    "binary_expression",
}

_LOGICAL_OPS: frozenset[str] = frozenset({"&&", "||", "and", "or"})

_FUNCTION_NODES: dict[str, set[str]] = {
    "python": {"function_definition"},
    "javascript": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "generator_function_declaration",
    },
    "jsx": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
    },
    "typescript": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "generator_function_declaration",
    },
    "tsx": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
    },
    "java": {"method_declaration", "constructor_declaration"},
}

_CLASS_NODES: dict[str, set[str]] = {
    "python": {"class_definition"},
    "javascript": {"class_declaration", "class_expression"},
    "jsx": {"class_declaration", "class_expression"},
    "typescript": {"class_declaration", "class_expression"},
    "tsx": {"class_declaration", "class_expression"},
    "java": {
        "class_declaration",
        "interface_declaration",
        "enum_declaration",
        "record_declaration",
    },
}


def _parse_with_tree_sitter(
    file_path: str,
    content: str,
    lang: str,
    ts_language: Any,
) -> ParseResult:
    """Parse *content* using tree-sitter and extract structural metrics."""
    from tree_sitter import Parser  # type: ignore[import]

    parser = Parser(ts_language)
    tree = parser.parse(content.encode("utf-8", errors="replace"))

    lines = content.splitlines()
    loc = len(lines)

    func_node_types = _FUNCTION_NODES.get(lang, set())
    class_node_types = _CLASS_NODES.get(lang, set())

    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    def _count_complexity(node: Any) -> int:
        count = 0
        if node.type in _COMPLEXITY_NODES:
            if node.type in ("binary_expression", "logical_expression", "boolean_operator"):
                for child in node.children:
                    text = child.text.decode() if child.text else ""
                    if text in _LOGICAL_OPS:
                        count += 1
            else:
                count += 1
        for child in node.children:
            count += _count_complexity(child)
        return count

    def _max_nesting(node: Any, depth: int = 0) -> int:
        is_block = node.type in _BLOCK_TYPES
        current = depth + (1 if is_block else 0)
        child_max = current
        for child in node.children:
            child_max = max(child_max, _max_nesting(child, current))
        return child_max

    def _has_docstring(node: Any) -> bool:
        if lang == "python":
            for child in node.children:
                if child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            for expr in stmt.children:
                                if expr.type in ("string", "concatenated_string"):
                                    return True
                        break
        elif lang in ("javascript", "jsx", "typescript", "tsx"):
            for child in node.children:
                if child.type in ("comment", "block_comment"):
                    return True
                if child.type == "statement_block":
                    for stmt in child.children:
                        if stmt.type in ("comment", "block_comment"):
                            return True
                    break
        return False

    def _function_name(node: Any) -> str:
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                return child.text.decode("utf-8", errors="replace") if child.text else "<anonymous>"
        return "<anonymous>"

    def _class_name(node: Any) -> str:
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf-8", errors="replace") if child.text else "<unknown>"
        return "<unknown>"

    def _method_count(node: Any) -> int:
        method_types = _FUNCTION_NODES.get(lang, set())
        count = 0

        def _walk(n: Any) -> None:
            nonlocal count
            if n.type in method_types:
                count += 1
            for child in n.children:
                _walk(child)

        for child in node.children:
            if child.type in ("block", "class_body", "declaration_list"):
                _walk(child)
        return count

    def _count_params(node: Any) -> int:
        for child in node.children:
            if child.type in ("parameters", "formal_parameters", "parameter_list"):
                params = [c for c in child.children if c.is_named and c.type != "comment"]
                count = len(params)
                if lang == "python" and params:
                    first_text = params[0].text
                    if first_text and first_text.decode() in ("self", "cls"):
                        count -= 1
                return max(0, count)
        return 0

    def _walk_top(node: Any) -> None:
        if node.type in func_node_types:
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            complexity = 1 + _count_complexity(node)
            nesting = max(0, _max_nesting(node) - 1)
            functions.append(
                FunctionMetrics(
                    name=_function_name(node),
                    file_path=file_path,
                    loc=end_line - start_line + 1,
                    complexity=complexity,
                    nesting_depth=nesting,
                    param_count=_count_params(node),
                    has_docstring=_has_docstring(node),
                )
            )
        elif node.type in class_node_types:
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            classes.append(
                ClassMetrics(
                    name=_class_name(node),
                    file_path=file_path,
                    method_count=_method_count(node),
                    loc=end_line - start_line + 1,
                )
            )

        for child in node.children:
            _walk_top(child)

    _walk_top(tree.root_node)

    max_complexity = max((f.complexity for f in functions), default=0)
    max_nesting = max((f.nesting_depth for f in functions), default=0)

    file_metrics = FileMetrics(
        file_path=file_path,
        language=lang,
        loc=loc,
        comment_ratio=_estimate_comment_ratio(content, lang),
        function_count=len(functions),
        class_count=len(classes),
        import_count=_count_imports(tree.root_node, lang),
        max_complexity=max_complexity,
        max_nesting=max_nesting,
    )

    return ParseResult(file_metrics=file_metrics, functions=functions, classes=classes)


def _count_imports(root: Any, lang: str) -> int:
    """Count import statements in the root node."""
    import_types: set[str] = set()
    if lang == "python":
        import_types = {"import_statement", "import_from_statement"}
    elif lang in ("javascript", "jsx", "typescript", "tsx"):
        import_types = {"import_statement", "import_declaration"}
    elif lang == "java":
        import_types = {"import_declaration"}

    count = 0

    def _walk(node: Any) -> None:
        nonlocal count
        if node.type in import_types:
            count += 1
        for child in node.children:
            _walk(child)

    _walk(root)
    return count


def _estimate_comment_ratio(content: str, lang: str) -> float:
    """Estimate the fraction of lines that are comments."""
    lines = content.splitlines()
    if not lines:
        return 0.0

    comment_count = 0
    in_block = False

    for line in lines:
        stripped = line.strip()
        if lang == "python":
            if stripped.startswith("#"):
                comment_count += 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                comment_count += 1
                if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                    in_block = not in_block
            elif in_block:
                comment_count += 1
        elif lang in ("javascript", "jsx", "typescript", "tsx", "java"):
            if stripped.startswith("//"):
                comment_count += 1
            elif stripped.startswith("/*"):
                comment_count += 1
                in_block = True
            elif in_block:
                comment_count += 1
                if "*/" in stripped:
                    in_block = False

    return comment_count / len(lines)


# ── Regex fallback ────────────────────────────────────────────────────────────


def _parse_with_regex(file_path: str, content: str, lang: str) -> ParseResult:
    """
    Regex-based metric extraction for when tree-sitter is unavailable.

    Less accurate than AST-based parsing but provides useful approximations.
    """
    lines = content.splitlines()
    loc = len(lines)

    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    if lang == "python":
        functions, classes = _regex_python(file_path, lines)
    elif lang in ("javascript", "jsx", "typescript", "tsx"):
        functions, classes = _regex_js_ts(file_path, lines)
    elif lang == "java":
        functions, classes = _regex_java(file_path, lines)

    file_metrics = FileMetrics(
        file_path=file_path,
        language=lang,
        loc=loc,
        comment_ratio=_estimate_comment_ratio(content, lang),
        function_count=len(functions),
        class_count=len(classes),
        import_count=_count_imports_regex(content, lang),
        max_complexity=max((f.complexity for f in functions), default=0),
        max_nesting=max((f.nesting_depth for f in functions), default=0),
    )

    return ParseResult(file_metrics=file_metrics, functions=functions, classes=classes)


# ── Python regex parser ───────────────────────────────────────────────────────

_PY_FUNC_RE = re.compile(r"^(\s{0,16})(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)")
_PY_CLASS_RE = re.compile(r"^(\s{0,8})class\s+(\w+)")
_PY_BRANCH_RE = re.compile(r"\b(if|elif|for|while|except|with|and|or)\b")
_PY_DOCSTRING_RE = re.compile(r'^\s*(?:"""|\'\'\').*')


def _regex_python(
    file_path: str, lines: list[str]
) -> tuple[list[FunctionMetrics], list[ClassMetrics]]:
    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    # (name, start_line, base_indent, param_count)
    func_stack: list[tuple[str, int, int, int]] = []
    # (name, start_line, base_indent)
    class_stack: list[tuple[str, int, int]] = []
    class_method_counts: dict[int, int] = {}

    def _flush_func(name: str, start: int, param_cnt: int, end: int) -> None:
        func_lines = lines[start:end]
        branch_count = sum(len(_PY_BRANCH_RE.findall(l)) for l in func_lines)
        first_body = lines[start + 1].strip() if start + 1 < len(lines) else ""
        functions.append(
            FunctionMetrics(
                name=name,
                file_path=file_path,
                loc=end - start,
                complexity=1 + branch_count,
                nesting_depth=_estimate_nesting_python(func_lines),
                param_count=param_cnt,
                has_docstring=bool(_PY_DOCSTRING_RE.match(first_body)),
            )
        )

    def _flush_class(name: str, start: int, end: int) -> None:
        classes.append(
            ClassMetrics(
                name=name,
                file_path=file_path,
                method_count=class_method_counts.pop(start, 0),
                loc=end - start,
            )
        )

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())

        # Close stale functions.
        still_open: list[tuple[str, int, int, int]] = []
        for item in func_stack:
            name, start, base_ind, param_cnt = item
            if indent <= base_ind and i > start:
                _flush_func(name, start, param_cnt, i)
            else:
                still_open.append(item)
        func_stack[:] = still_open

        # Close stale classes.
        still_open_cls: list[tuple[str, int, int]] = []
        for item in class_stack:
            cname, cstart, cind = item
            if indent <= cind and i > cstart:
                _flush_class(cname, cstart, i)
            else:
                still_open_cls.append(item)
        class_stack[:] = still_open_cls

        fm = _PY_FUNC_RE.match(line)
        if fm:
            raw_params = [p.strip() for p in fm.group(3).split(",") if p.strip()]
            param_cnt = len([p for p in raw_params if p not in ("self", "cls")])
            func_stack.append((fm.group(2), i, indent, param_cnt))
            if class_stack:
                class_method_counts[class_stack[-1][1]] = (
                    class_method_counts.get(class_stack[-1][1], 0) + 1
                )

        cm = _PY_CLASS_RE.match(line)
        if cm:
            class_stack.append((cm.group(2), i, indent))
            class_method_counts[i] = 0

    eof = len(lines)
    for name, start, _, param_cnt in func_stack:
        _flush_func(name, start, param_cnt, eof)
    for cname, cstart, _ in class_stack:
        _flush_class(cname, cstart, eof)

    return functions, classes


def _estimate_nesting_python(lines: list[str]) -> int:
    """Estimate max nesting depth from indentation differences."""
    if not lines:
        return 0
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return 0
    base = len(non_empty[0]) - len(non_empty[0].lstrip())
    max_depth = 0
    for line in non_empty:
        depth = max(0, (len(line) - len(line.lstrip()) - base) // 4)
        max_depth = max(max_depth, depth)
    return max_depth


# ── JS/TS regex parser ────────────────────────────────────────────────────────

_JS_FUNC_RE = re.compile(
    r"(?:function\s+(\w+)\s*\(|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))"
)
_JS_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
_JS_BRANCH_RE = re.compile(
    r"\b(if|else\s+if|for|while|catch|switch|case)\b|&&|\|\||\?(?![\?:])"
)


def _regex_js_ts(
    file_path: str, lines: list[str]
) -> tuple[list[FunctionMetrics], list[ClassMetrics]]:
    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    brace_depth = 0
    func_stack: list[tuple[str, int, int]] = []  # (name, start, open_depth)
    class_stack: list[tuple[str, int, int]] = []

    for i, line in enumerate(lines):
        opens = line.count("{")
        closes = line.count("}")

        fm = _JS_FUNC_RE.search(line)
        if fm and "{" in line:
            name = fm.group(1) or fm.group(2) or "<anonymous>"
            func_stack.append((name, i, brace_depth))

        cm = _JS_CLASS_RE.search(line)
        if cm and "{" in line:
            class_stack.append((cm.group(1), i, brace_depth))

        brace_depth += opens - closes

        closed_f = [idx for idx, (_, start, d) in enumerate(func_stack) if brace_depth <= d and i > start]
        for idx in reversed(closed_f):
            name, start, _ = func_stack.pop(idx)
            func_lines = lines[start : i + 1]
            func_loc = i - start + 1
            branch_count = sum(len(_JS_BRANCH_RE.findall(l)) for l in func_lines)
            param_match = re.search(r"\(([^)]*)\)", lines[start])
            raw = param_match.group(1) if param_match else ""
            param_count = len([p for p in raw.split(",") if p.strip()])
            functions.append(
                FunctionMetrics(
                    name=name,
                    file_path=file_path,
                    loc=func_loc,
                    complexity=1 + branch_count,
                    nesting_depth=min(branch_count, 10),
                    param_count=param_count,
                    has_docstring="/**" in (lines[max(0, start - 1)]),
                )
            )

        closed_c = [idx for idx, (_, cstart, d) in enumerate(class_stack) if brace_depth <= d and i > cstart]
        for idx in reversed(closed_c):
            cname, cstart, _ = class_stack.pop(idx)
            cls_loc = i - cstart + 1
            method_count = sum(
                1 for l in lines[cstart : i + 1]
                if re.search(r"(?:async\s+)?\w+\s*\([^)]*\)\s*\{", l)
            )
            classes.append(
                ClassMetrics(
                    name=cname,
                    file_path=file_path,
                    method_count=method_count,
                    loc=cls_loc,
                )
            )

    return functions, classes


# ── Java regex parser ─────────────────────────────────────────────────────────

_JAVA_METHOD_RE = re.compile(
    r"\b(?:(?:public|private|protected|static|final|synchronized|abstract|native)\s+)*"
    r"(?:(?:<[^>]+>\s+)?(?:void|\w+(?:<[^>]*>)?))\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\{"
)
_JAVA_CLASS_RE = re.compile(
    r"\b(?:(?:public|private|protected|abstract|final|static)\s+)*class\s+(\w+)"
)
_JAVA_BRANCH_RE = re.compile(r"\b(if|else\s+if|for|while|catch|case)\b|&&|\|\|")


def _regex_java(
    file_path: str, lines: list[str]
) -> tuple[list[FunctionMetrics], list[ClassMetrics]]:
    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    brace_depth = 0
    method_stack: list[tuple[str, int, int]] = []
    class_stack: list[tuple[str, int, int]] = []

    for i, line in enumerate(lines):
        opens = line.count("{")
        closes = line.count("}")

        mm = _JAVA_METHOD_RE.search(line)
        if mm:
            method_stack.append((mm.group(1), i, brace_depth))

        cm = _JAVA_CLASS_RE.search(line)
        if cm and "{" in line:
            class_stack.append((cm.group(1), i, brace_depth))

        brace_depth += opens - closes

        closed_m = [idx for idx, (_, start, d) in enumerate(method_stack) if brace_depth <= d and i > start]
        for idx in reversed(closed_m):
            name, start, _ = method_stack.pop(idx)
            func_lines = lines[start : i + 1]
            func_loc = i - start + 1
            branch_count = sum(len(_JAVA_BRANCH_RE.findall(l)) for l in func_lines)
            param_match = re.search(r"\(([^)]*)\)", lines[start])
            raw = param_match.group(1) if param_match else ""
            param_count = len([p for p in raw.split(",") if p.strip()])
            functions.append(
                FunctionMetrics(
                    name=name,
                    file_path=file_path,
                    loc=func_loc,
                    complexity=1 + branch_count,
                    nesting_depth=0,
                    param_count=param_count,
                    has_docstring="/**" in (lines[max(0, start - 1)]),
                )
            )

        closed_c = [idx for idx, (_, cstart, d) in enumerate(class_stack) if brace_depth <= d and i > cstart]
        for idx in reversed(closed_c):
            cname, cstart, _ = class_stack.pop(idx)
            method_count = sum(1 for f in functions)
            classes.append(
                ClassMetrics(
                    name=cname,
                    file_path=file_path,
                    method_count=method_count,
                    loc=i - cstart + 1,
                )
            )

    return functions, classes


def _count_imports_regex(content: str, lang: str) -> int:
    """Count import statements via regex."""
    if lang == "python":
        return len(re.findall(r"^\s*(?:import|from)\s+\w+", content, re.MULTILINE))
    if lang in ("javascript", "jsx", "typescript", "tsx", "java"):
        return len(re.findall(r"^\s*import\s+", content, re.MULTILINE))
    return 0
