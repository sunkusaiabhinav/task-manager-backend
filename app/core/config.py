"""
Core configuration — reads from environment variables / .env file.

Uses Pydantic Settings so that:
- Missing required vars cause an immediate, clear startup error
- Values are type-validated (str, int, bool, etc.)
- .env file is loaded automatically in development
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application configuration lives here.

    Priority order (highest → lowest):
      1. Actual environment variables set in the shell
      2. Values from the .env file
      3. Default values defined below
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # silently ignore unknown env vars
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "Task Manager API"
    app_env: str = "development"  # development | staging | production
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./taskmanager.db"

    # ── Derived helpers ──────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "testing"


# Single shared instance — import this everywhere
settings = Settings()
