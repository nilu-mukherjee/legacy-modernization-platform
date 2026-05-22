"""
Application Configuration
=========================

Centralised settings loaded from environment variables via **pydantic-settings**.
Every configurable value lives here so that the rest of the codebase never reads
``os.environ`` directly.

Usage::

    from app.core.config import settings
    print(settings.APP_NAME)
"""

from __future__ import annotations

import json
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings.

    Values are populated from environment variables (or an ``.env`` file at the
    project root).  Defaults are provided for development convenience; every
    deployment **must** supply production values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "CodeLens AI"
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://codelens:codelens@localhost:5432/codelens"
    DATABASE_SYNC_URL: str = "postgresql://codelens:codelens@localhost:5432/codelens"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Authentication (GitHub OAuth) ────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    AUTH_SECRET: str = "change-me-in-production"

    # ── AI Providers ─────────────────────────────────────────────────────
    AI_PROVIDER: str = "anthropic"  # "anthropic" | "openai"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_FAST: str = "claude-sonnet-4-20250514"
    AI_MODEL_POWERFUL: str = "claude-sonnet-4-20250514"

    # ── Encryption ───────────────────────────────────────────────────────
    ENCRYPTION_KEY: str = ""

    # ── Repository Analysis Limits ───────────────────────────────────────
    MAX_REPO_SIZE_MB: int = 500
    MAX_FILES_TO_PARSE: int = 5000
    MAX_FILE_SIZE_KB: int = 1024
    CLONE_TIMEOUT_SECONDS: int = 120
    ANALYSIS_TIMEOUT_SECONDS: int = 600

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Singleton — import this from anywhere in the app.
settings = Settings()
