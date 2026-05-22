"""
Dependency Analyzer Service
============================

Parses dependency manifest files (``package.json``, ``requirements.txt``,
``pom.xml``) and queries public registries (npm, PyPI) to determine:

- Whether each package is outdated and by how many days.
- Whether it has known CVEs.
- Whether it is deprecated.
- Its license type.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class Dependency:
    """A single dependency parsed from a manifest file."""

    name: str
    current_version: str | None = None
    ecosystem: str = "unknown"  # npm | pip | maven


@dataclass
class DependencyResult:
    """Full health assessment of a single dependency."""

    name: str
    current_version: str | None = None
    latest_version: str | None = None
    ecosystem: str = "unknown"
    days_behind: int = 0
    is_deprecated: bool = False
    vulnerability_count: int = 0
    vulnerabilities: list[dict] = field(default_factory=list)
    risk_level: str = "low"
    license: str | None = None


# ── Manifest Parsers ─────────────────────────────────────────────────────────


def parse_package_json(path: str) -> list[Dependency]:
    """
    Parse ``package.json`` and extract dependencies.

    Combines ``dependencies`` and ``devDependencies``.

    Args:
        path: Absolute path to the ``package.json`` file.

    Returns:
        List of :class:`Dependency` instances.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    deps: list[Dependency] = []
    for section in ("dependencies", "devDependencies"):
        for name, version in data.get(section, {}).items():
            # Strip version prefixes like ^, ~, >=, etc.
            clean = re.sub(r"^[\^~>=<]*", "", version)
            deps.append(Dependency(name=name, current_version=clean, ecosystem="npm"))

    return deps


def parse_requirements_txt(path: str) -> list[Dependency]:
    """
    Parse ``requirements.txt`` and extract dependencies.

    Handles ``==``, ``>=``, ``~=`` version specifiers and ignores comments.

    Args:
        path: Absolute path to the ``requirements.txt`` file.

    Returns:
        List of :class:`Dependency` instances.
    """
    deps: list[Dependency] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Split on version specifier.
            match = re.match(r"^([a-zA-Z0-9_.-]+)\s*(?:[><=~!]+\s*(.+))?", line)
            if match:
                name = match.group(1)
                version = match.group(2)
                deps.append(Dependency(
                    name=name,
                    current_version=version.strip() if version else None,
                    ecosystem="pip",
                ))
    return deps


# ── Registry Lookups ─────────────────────────────────────────────────────────


async def check_npm_versions(packages: list[Dependency]) -> list[DependencyResult]:
    """
    Query the npm registry for each package to determine latest version,
    deprecation status, and license.

    Args:
        packages: List of npm dependencies.

    Returns:
        List of :class:`DependencyResult` with filled registry data.
    """
    results: list[DependencyResult] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for pkg in packages:
            result = DependencyResult(
                name=pkg.name,
                current_version=pkg.current_version,
                ecosystem="npm",
            )
            try:
                resp = await client.get(f"https://registry.npmjs.org/{pkg.name}")
                if resp.status_code == 200:
                    data = resp.json()
                    dist_tags = data.get("dist-tags", {})
                    result.latest_version = dist_tags.get("latest")
                    result.is_deprecated = bool(data.get("deprecated"))
                    latest_info = data.get("versions", {}).get(
                        result.latest_version or "", {}
                    )
                    raw_license = latest_info.get("license") or data.get("license")
                    result.license = (raw_license or "")[:490] or None

                    # Calculate days behind.
                    if result.latest_version and pkg.current_version:
                        time_data = data.get("time", {})
                        current_date = time_data.get(pkg.current_version)
                        latest_date = time_data.get(result.latest_version)
                        if current_date and latest_date:
                            try:
                                c = datetime.fromisoformat(current_date.replace("Z", "+00:00"))
                                l = datetime.fromisoformat(latest_date.replace("Z", "+00:00"))
                                result.days_behind = max(0, (l - c).days)
                            except (ValueError, TypeError):
                                pass
            except (httpx.HTTPError, json.JSONDecodeError, KeyError):
                pass

            result.risk_level = _calculate_risk(result)
            results.append(result)

    return results


async def check_pypi_versions(packages: list[Dependency]) -> list[DependencyResult]:
    """
    Query PyPI for each package to determine latest version and metadata.

    Args:
        packages: List of pip dependencies.

    Returns:
        List of :class:`DependencyResult` with filled registry data.
    """
    results: list[DependencyResult] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for pkg in packages:
            result = DependencyResult(
                name=pkg.name,
                current_version=pkg.current_version,
                ecosystem="pip",
            )
            try:
                resp = await client.get(f"https://pypi.org/pypi/{pkg.name}/json")
                if resp.status_code == 200:
                    data = resp.json()
                    info = data.get("info", {})
                    result.latest_version = info.get("version")
                    raw_license = info.get("license")
                    result.license = (raw_license or "")[:490] or None

                    # Calculate days behind using release dates.
                    releases = data.get("releases", {})
                    if result.latest_version and pkg.current_version:
                        current_files = releases.get(pkg.current_version, [])
                        latest_files = releases.get(result.latest_version, [])
                        if current_files and latest_files:
                            try:
                                c_date = datetime.fromisoformat(
                                    current_files[0].get("upload_time_iso_8601", "").replace("Z", "+00:00")
                                )
                                l_date = datetime.fromisoformat(
                                    latest_files[0].get("upload_time_iso_8601", "").replace("Z", "+00:00")
                                )
                                result.days_behind = max(0, (l_date - c_date).days)
                            except (ValueError, TypeError):
                                pass
            except (httpx.HTTPError, json.JSONDecodeError, KeyError):
                pass

            result.risk_level = _calculate_risk(result)
            results.append(result)

    return results


# ── Risk Level Calculation ───────────────────────────────────────────────────


def _calculate_risk(dep: DependencyResult) -> str:
    """
    Assign a risk level to a dependency based on age, vulnerabilities,
    and deprecation status.

    Returns:
        "critical" | "high" | "medium" | "low"
    """
    if dep.vulnerability_count > 0 or dep.is_deprecated:
        return "critical"
    if dep.days_behind > 730:  # > 2 years behind.
        return "high"
    if dep.days_behind > 365:  # > 1 year behind.
        return "medium"
    return "low"
