# ABOUTME: Tests for settings and configuration management
# ABOUTME: Tests environment variable loading, validation, and singleton pattern

import os
from pathlib import Path

import pytest


def test_settings_class_exists():
    """Test that Settings class can be imported from config."""
    from src.config import Settings

    assert Settings is not None


def test_settings_loads_from_environment(monkeypatch):
    """Test that settings load from environment variables."""
    from src.config import Settings

    # Set test environment variables
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")

    settings = Settings()

    assert settings.app_name == "Test App"
    assert settings.environment == "development"
    assert settings.database_url == "postgresql://test:test@localhost:5432/test"
    assert settings.redis_url == "redis://localhost:6379"
    assert settings.secret_key == "test-secret-key-min-32-chars-long"


def test_settings_has_default_values(monkeypatch):
    """Test that settings have sensible defaults."""
    from src.config import Settings

    # Set only required fields
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")

    settings = Settings()

    assert settings.app_name == "AI Executive Assistant"
    assert settings.environment == "development"
    assert settings.debug is False


def test_settings_validates_environment_enum(monkeypatch):
    """Test that environment must be one of valid values."""
    from src.config import Settings

    monkeypatch.setenv("ENVIRONMENT", "invalid-env")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")

    with pytest.raises(ValueError):
        Settings()


def test_settings_requires_database_url(monkeypatch):
    """Test that database_url is required."""
    from src.config import Settings

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError):
        Settings()


def test_settings_requires_secret_key(monkeypatch):
    """Test that secret_key is required."""
    from src.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        Settings()


def test_settings_optional_oauth_fields(monkeypatch):
    """Test that OAuth fields are optional."""
    from src.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")

    settings = Settings()

    assert settings.google_client_id is None
    assert settings.google_client_secret is None
    assert settings.slack_bot_token is None
    assert settings.slack_signing_secret is None


def test_settings_loads_oauth_credentials(monkeypatch):
    """Test that OAuth credentials load when provided."""
    from src.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-min-32-chars-long")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-secret")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-signing-secret")

    settings = Settings()

    assert settings.google_client_id == "test-google-id"
    assert settings.google_client_secret == "test-google-secret"
    assert settings.slack_bot_token == "xoxb-test-token"
    assert settings.slack_signing_secret == "test-signing-secret"


def test_settings_loads_from_env_file():
    """Test that settings can load from .env file."""
    from src.config import Settings

    # Create temporary .env file
    env_path = Path(".env.test")
    env_path.write_text(
        """
APP_NAME=Test App from File
ENVIRONMENT=staging
DATABASE_URL=postgresql://file:file@localhost:5432/file
REDIS_URL=redis://localhost:6379
SECRET_KEY=test-secret-key-from-file-32chars
"""
    )

    try:
        settings = Settings(_env_file=str(env_path))

        assert settings.app_name == "Test App from File"
        assert settings.environment == "staging"
    finally:
        # Cleanup
        if env_path.exists():
            env_path.unlink()


def test_settings_version_exists():
    """Test that version field exists and has a value."""
    from src.config import Settings

    # Use environment variables for required fields
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long")

    settings = Settings()

    assert hasattr(settings, "version")
    assert settings.version is not None
    assert isinstance(settings.version, str)


def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    from src.config import get_settings

    # Use environment variables for required fields
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long")

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
