"""
CodeLens AI — Application Configuration.

Centralised settings management via Pydantic Settings.  All values are read
from environment variables (or an ``.env`` file in the project root) and
validated at startup.  This guarantees the application fails fast when a
required secret is missing rather than blowing up at runtime.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables.

    The field names correspond **exactly** to the env-var names defined in
    ``.env.example``.  Pydantic Settings handles type coercion automatically
    (e.g. ``str`` → ``int``, comma-separated string → ``list[str]``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Silently ignore env vars we don't define here
    )

    # ── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "CodeLens AI"
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://codelens:codelens@localhost:5432/codelens"
    DATABASE_SYNC_URL: str = "postgresql://codelens:codelens@localhost:5432/codelens"

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── GitHub OAuth ─────────────────────────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    AUTH_SECRET: str = "change-me-in-production"

    # ── AI Provider ──────────────────────────────────────────────────────────
    AI_PROVIDER: str = "anthropic"  # "anthropic" | "openai"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_FAST: str = "claude-sonnet-4-20250514"
    AI_MODEL_POWERFUL: str = "claude-sonnet-4-20250514"

    # ── Encryption ───────────────────────────────────────────────────────────
    ENCRYPTION_KEY: str = ""

    # ── Repository Analysis Limits ───────────────────────────────────────────
    MAX_REPO_SIZE_MB: int = 500
    MAX_FILES_TO_PARSE: int = 5000
    MAX_FILE_SIZE_KB: int = 1024
    CLONE_TIMEOUT_SECONDS: int = 120
    ANALYSIS_TIMEOUT_SECONDS: int = 600

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Derived / Computed helpers ───────────────────────────────────────────

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Accept both a comma-separated string and an actual list.

        The ``.env`` file stores origins as a single string
        ``http://localhost:3000,http://localhost:3001`` while tests may pass a
        native Python list.

        Args:
            v: Raw value from the environment.

        Returns:
            A list of allowed origin URLs.
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Return ``True`` when running in the production environment."""
        return self.APP_ENV == "production"


# ---------------------------------------------------------------------------
# Module-level singleton — import ``settings`` from anywhere in the app.
# ---------------------------------------------------------------------------
settings = Settings()
