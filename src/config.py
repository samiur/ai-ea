# ABOUTME: Application settings and configuration management
# ABOUTME: Uses pydantic-settings for environment variable loading and validation

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_version() -> str:
    """Get version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            project_data = data.get("project")
            if project_data and isinstance(project_data, dict):
                version = project_data.get("version", "0.1.0")
                if isinstance(version, str):
                    return version
    return "0.1.0"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: Annotated[str, Field(description="Application name")] = "AI Executive Assistant"
    version: Annotated[str, Field(description="Application version")] = Field(
        default_factory=_get_version
    )
    environment: Annotated[
        Literal["development", "staging", "production"],
        Field(description="Deployment environment"),
    ] = "development"
    debug: Annotated[bool, Field(description="Debug mode enabled")] = False

    # Required infrastructure
    database_url: Annotated[str, Field(description="PostgreSQL database URL")]
    redis_url: Annotated[str, Field(description="Redis connection URL")]
    secret_key: Annotated[
        str, Field(description="Secret key for JWT and encryption", min_length=32)
    ]

    # Optional OAuth credentials
    google_client_id: Annotated[str | None, Field(description="Google OAuth client ID")] = None
    google_client_secret: Annotated[str | None, Field(description="Google OAuth client secret")] = (
        None
    )
    slack_bot_token: Annotated[str | None, Field(description="Slack bot OAuth token")] = None
    slack_signing_secret: Annotated[
        str | None, Field(description="Slack signing secret for webhooks")
    ] = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
