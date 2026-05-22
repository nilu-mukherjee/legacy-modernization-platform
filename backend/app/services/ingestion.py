"""
Repository Ingestion Service
=============================

Handles cloning GitHub repositories, walking the file tree, detecting
languages, and parsing dependency manifests.

This is **Stage 1 & 2** of the analysis pipeline.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.core.config import settings

# ── Constants ────────────────────────────────────────────────────────────────

# Directories to skip during file-tree walks.
SKIP_DIRS: set[str] = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "vendor", "target", ".idea",
    ".vscode", "coverage", ".nyc_output", "eggs", ".eggs",
    ".tox", "bower_components",
}

# Map file extensions to human-readable language names.
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".ipynb": "jupyter notebook",
    ".sh": "shell",
    ".bash": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "scss",
    ".md": "markdown",
    ".mako": "mako",
    ".mak": "mako",
    ".mk": "makefile",
    ".dockerfile": "dockerfile",
}

# Known dependency manifest filenames.
MANIFEST_FILES: set[str] = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "pom.xml",
    "build.gradle",
    "Gemfile",
    "go.mod",
    "Cargo.toml",
    "composer.json",
}


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class FileInfo:
    """Metadata for a single file discovered during inventory."""

    path: str  # Relative path within the repo.
    extension: str
    language: str | None
    loc: int
    size_bytes: int


@dataclass
class Inventory:
    """Complete file inventory for a cloned repository."""

    files: list[FileInfo] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_loc: int = 0
    manifests: dict[str, str] = field(default_factory=dict)  # filename → full path
    has_readme: bool = False
    has_dockerfile: bool = False
    has_ci_config: bool = False
    has_test_dir: bool = False
    has_linter_config: bool = False
    has_env_example: bool = False


# ── Public API ───────────────────────────────────────────────────────────────


def clone_repository(
    repo_url: str,
    target_dir: str,
    access_token: Optional[str] = None,
    *,
    depth: int = 1,
    timeout: int | None = None,
) -> str:
    """
    Shallow-clone a GitHub repository into *target_dir*.

    Args:
        repo_url: HTTPS URL of the repository.
        target_dir: Local directory to clone into.
        access_token: GitHub OAuth token for private repos.
        depth: Git clone depth (default 1 = latest commit only).
        timeout: Seconds before the clone is killed.

    Returns:
        The *target_dir* path.

    Raises:
        RuntimeError: if the ``git clone`` process fails.
    """
    timeout = timeout or settings.CLONE_TIMEOUT_SECONDS
    clone_url = repo_url

    if access_token:
        # Inject token for private repository access.
        clone_url = repo_url.replace(
            "https://", f"https://x-access-token:{access_token}@"
        )

    cmd = [
        "git", "clone",
        "--depth", str(depth),
        "--single-branch",
        clone_url,
        target_dir,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr.strip()}")

    return target_dir


def build_file_inventory(repo_path: str) -> Inventory:
    """
    Walk the repository tree and build a complete file inventory.

    Skips binary files, ignored directories, and files exceeding the
    configured size limit.

    Args:
        repo_path: Absolute path to the cloned repository.

    Returns:
        An :class:`Inventory` with file info, language stats, and manifest
        locations.
    """
    inventory = Inventory()
    max_size = settings.MAX_FILE_SIZE_KB * 1024  # Convert to bytes.

    for root, dirs, files in os.walk(repo_path):
        # Prune ignored directories in-place.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        # Detect special directories.
        for d in dirs:
            if d.lower() in ("test", "tests", "__tests__", "spec", "specs"):
                inventory.has_test_dir = True

        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, repo_path)
            ext = Path(filename).suffix.lower()

            # Detect special files.
            lower_name = filename.lower()
            if lower_name.startswith("readme"):
                inventory.has_readme = True
            if lower_name in ("dockerfile", "dockerfile.dev"):
                inventory.has_dockerfile = True
            if lower_name in (".env.example", ".env.sample"):
                inventory.has_env_example = True
            if lower_name in (
                ".eslintrc", ".eslintrc.js", ".eslintrc.json",
                "ruff.toml", ".flake8", ".pylintrc", "setup.cfg",
            ):
                inventory.has_linter_config = True

            # CI/CD detection.
            if ".github/workflows" in rel_path or lower_name in (
                ".gitlab-ci.yml", ".circleci", "Jenkinsfile",
            ):
                inventory.has_ci_config = True

            # Record manifests.
            if filename in MANIFEST_FILES:
                inventory.manifests[filename] = filepath

            # Get file size.
            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue

            if size > max_size:
                continue  # Skip oversized files.

            # Count lines.
            # Bare filenames with no extension (Dockerfile, Makefile, etc.)
            if not ext and lower_name in ("dockerfile", "dockerfile.dev"):
                language = "dockerfile"
            elif not ext and lower_name in ("makefile", "gnumakefile"):
                language = "makefile"
            else:
                language = LANGUAGE_MAP.get(ext)
            loc = 0
            if language and language not in ("json", "xml", "yaml", "markdown"):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        loc = sum(1 for line in f if line.strip())
                except (OSError, UnicodeDecodeError):
                    continue

            file_info = FileInfo(
                path=rel_path,
                extension=ext,
                language=language,
                loc=loc,
                size_bytes=size,
            )
            inventory.files.append(file_info)
            inventory.total_files += 1
            inventory.total_loc += loc

            if language:
                inventory.languages[language] = (
                    inventory.languages.get(language, 0) + size
                )

    return inventory


def detect_languages(inventory: Inventory) -> dict[str, int]:
    """
    Return a mapping of language → LOC, sorted by LOC descending.

    Filters out data/config formats that GitHub also excludes from breakdowns.
    """
    source_langs = {
        k: v
        for k, v in inventory.languages.items()
        if k not in ("json", "xml", "yaml", "markdown")
    }
    return dict(sorted(source_langs.items(), key=lambda x: x[1], reverse=True))
