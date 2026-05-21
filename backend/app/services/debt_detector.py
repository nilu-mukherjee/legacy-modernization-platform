"""
Technical Debt Detection Service
================================

Rule-engine that scans AST-extracted metrics and file contents for known
code smells, anti-patterns, and security issues.

Rules are defined as simple dicts in :data:`DEBT_RULES`. Each rule has:
    - ``id``       — unique identifier (e.g. ``COMPLEXITY_HIGH``).
    - ``category`` — complexity | style | architecture | security | documentation.
    - ``severity`` — low | medium | high | critical.
    - ``title``    — human-readable title template.
    - ``suggestion`` — actionable fix guidance.

The detector runs every rule against every file's metrics and produces a
flat list of :class:`DebtFinding` instances.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class FunctionMetrics:
    """Metrics for a single function, extracted by the AST parser."""

    name: str
    file_path: str
    loc: int = 0
    complexity: int = 1
    nesting_depth: int = 0
    param_count: int = 0
    has_docstring: bool = False


@dataclass
class ClassMetrics:
    """Metrics for a single class, extracted by the AST parser."""

    name: str
    file_path: str
    method_count: int = 0
    loc: int = 0


@dataclass
class FileMetrics:
    """Aggregate metrics for a single source file."""

    file_path: str
    language: str
    loc: int = 0
    comment_ratio: float = 0.0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    max_complexity: int = 0
    max_nesting: int = 0


@dataclass
class DebtFinding:
    """A single technical debt finding produced by the rule engine."""

    rule_id: str
    category: str
    severity: str
    title: str
    description: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    suggestion: str = ""
    estimated_hours: float = 0.0


# ── Security Regex Patterns ─────────────────────────────────────────────────

_SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}", "Possible hardcoded secret"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
    (r"(?i)sk-[0-9a-zA-Z]{20,}", "Possible API secret key"),
]

_SECURITY_PATTERNS = [
    (r"\beval\s*\(", "security", "critical", "Usage of eval()", "eval() executes arbitrary code — replace with safe alternatives"),
    (r"\bexec\s*\(", "security", "high", "Usage of exec()", "exec() executes arbitrary code — use AST-based approaches instead"),
    (r"(?i)cursor\.execute\s*\([^)]*%s", "security", "medium", "Possible SQL injection (string formatting)", "Use parameterized queries instead of string interpolation"),
    (r"(?i)cursor\.execute\s*\([^)]*\+", "security", "high", "Possible SQL injection (concatenation)", "Use parameterized queries"),
    (r"(?i)subprocess\.call\s*\(.*shell\s*=\s*True", "security", "high", "Shell injection risk", "Avoid shell=True; pass args as a list"),
]


# ── Rule Engine ──────────────────────────────────────────────────────────────


def detect_function_debt(func: FunctionMetrics) -> list[DebtFinding]:
    """
    Run function-level debt rules against a single function's metrics.

    Args:
        func: Metrics for one function / method.

    Returns:
        Zero or more :class:`DebtFinding` instances.
    """
    findings: list[DebtFinding] = []

    # High complexity
    if func.complexity > 20:
        findings.append(DebtFinding(
            rule_id="COMPLEXITY_CRITICAL",
            category="complexity",
            severity="critical",
            title=f"Critical cyclomatic complexity ({func.complexity})",
            description=f"Function '{func.name}' has {func.complexity} independent paths — extremely hard to test and maintain.",
            file_path=func.file_path,
            suggestion="Urgent refactoring: extract methods, use strategy pattern, or simplify conditionals.",
            estimated_hours=4.0,
        ))
    elif func.complexity > 10:
        findings.append(DebtFinding(
            rule_id="COMPLEXITY_HIGH",
            category="complexity",
            severity="high",
            title=f"High cyclomatic complexity ({func.complexity})",
            description=f"Function '{func.name}' has {func.complexity} independent paths.",
            file_path=func.file_path,
            suggestion="Break into smaller, focused functions with single responsibilities.",
            estimated_hours=2.0,
        ))

    # Long function
    if func.loc > 150:
        findings.append(DebtFinding(
            rule_id="VERY_LONG_FUNCTION",
            category="complexity",
            severity="high",
            title=f"Very long function ({func.loc} lines)",
            description=f"Function '{func.name}' is {func.loc} lines — extremely hard to understand.",
            file_path=func.file_path,
            suggestion="Apply SRP: extract helper functions, use early returns.",
            estimated_hours=3.0,
        ))
    elif func.loc > 60:
        findings.append(DebtFinding(
            rule_id="LONG_FUNCTION",
            category="complexity",
            severity="medium",
            title=f"Long function ({func.loc} lines)",
            description=f"Function '{func.name}' exceeds 60 lines.",
            file_path=func.file_path,
            suggestion="Functions should be < 60 lines. Extract helper functions.",
            estimated_hours=1.0,
        ))

    # Deep nesting
    if func.nesting_depth > 4:
        findings.append(DebtFinding(
            rule_id="DEEP_NESTING",
            category="complexity",
            severity="medium",
            title=f"Deeply nested code ({func.nesting_depth} levels)",
            description=f"Function '{func.name}' has {func.nesting_depth} levels of nesting.",
            file_path=func.file_path,
            suggestion="Use early returns, extract conditions, or apply guard clauses.",
            estimated_hours=1.0,
        ))

    # Too many parameters
    if func.param_count > 5:
        findings.append(DebtFinding(
            rule_id="TOO_MANY_PARAMS",
            category="style",
            severity="medium",
            title=f"Too many parameters ({func.param_count})",
            description=f"Function '{func.name}' accepts {func.param_count} parameters.",
            file_path=func.file_path,
            suggestion="Use a configuration object, dataclass, or builder pattern.",
            estimated_hours=1.0,
        ))

    # Missing docstring (only for non-trivial functions)
    if not func.has_docstring and func.loc > 10:
        findings.append(DebtFinding(
            rule_id="NO_DOCSTRING",
            category="documentation",
            severity="low",
            title="Public function missing documentation",
            description=f"Function '{func.name}' ({func.loc} lines) has no docstring.",
            file_path=func.file_path,
            suggestion="Add a docstring describing purpose, parameters, and return value.",
            estimated_hours=0.25,
        ))

    return findings


def detect_class_debt(cls: ClassMetrics) -> list[DebtFinding]:
    """Run class-level debt rules."""
    findings: list[DebtFinding] = []

    if cls.method_count > 20:
        findings.append(DebtFinding(
            rule_id="GOD_CLASS",
            category="architecture",
            severity="high",
            title=f"God class with {cls.method_count} methods",
            description=f"Class '{cls.name}' has {cls.method_count} methods — likely violates SRP.",
            file_path=cls.file_path,
            suggestion="Split into smaller, focused classes following Single Responsibility Principle.",
            estimated_hours=8.0,
        ))

    return findings


def detect_file_debt(file_metrics: FileMetrics) -> list[DebtFinding]:
    """Run file-level debt rules."""
    findings: list[DebtFinding] = []

    if file_metrics.loc > 500:
        findings.append(DebtFinding(
            rule_id="LARGE_FILE",
            category="architecture",
            severity="medium",
            title=f"Large file ({file_metrics.loc} lines)",
            description=f"File '{file_metrics.file_path}' has {file_metrics.loc} lines.",
            file_path=file_metrics.file_path,
            suggestion="Consider splitting into multiple modules by responsibility.",
            estimated_hours=2.0,
        ))

    return findings


def detect_security_issues(file_path: str, content: str) -> list[DebtFinding]:
    """
    Scan file content for security issues using regex patterns.

    Detects hardcoded secrets, eval/exec usage, SQL injection patterns,
    and shell injection risks.
    """
    findings: list[DebtFinding] = []

    # Check for hardcoded secrets.
    for pattern, desc in _SECRET_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count("\n") + 1
            findings.append(DebtFinding(
                rule_id="HARDCODED_SECRET",
                category="security",
                severity="critical",
                title=desc,
                description=f"Potential secret found in {file_path} at line {line_num}.",
                file_path=file_path,
                line_start=line_num,
                suggestion="Move secrets to environment variables or a secrets manager.",
                estimated_hours=0.5,
            ))

    # Check for security anti-patterns.
    for pattern, category, severity, title, suggestion in _SECURITY_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count("\n") + 1
            findings.append(DebtFinding(
                rule_id=title.upper().replace(" ", "_").replace("(", "").replace(")", ""),
                category=category,
                severity=severity,
                title=title,
                description=f"Found in {file_path} at line {line_num}.",
                file_path=file_path,
                line_start=line_num,
                suggestion=suggestion,
                estimated_hours=1.0,
            ))

    return findings
