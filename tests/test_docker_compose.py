# ABOUTME: Tests for local development database setup (Step 9)
# ABOUTME: Validates docker-compose config, helper scripts, and env documentation

import os
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def compose(repo_root: Path) -> dict[str, Any]:
    """Load the parsed docker-compose file."""
    path = repo_root / "docker-compose.yml"
    assert path.exists(), "docker-compose.yml should exist"
    with open(path) as f:
        config: dict[str, Any] = yaml.safe_load(f)
    return config


@pytest.fixture
def postgres_service(compose: dict[str, Any]) -> dict[str, Any]:
    """Get the postgres service definition."""
    services = compose.get("services", {})
    assert "postgres" in services, "Compose should define a postgres service"
    service: dict[str, Any] = services["postgres"]
    return service


def test_postgres_uses_version_15(postgres_service: dict[str, Any]) -> None:
    """Test that local postgres matches the CI service version."""
    assert postgres_service["image"].startswith("postgres:15"), "Should use postgres:15"


def test_postgres_has_healthcheck(postgres_service: dict[str, Any]) -> None:
    """Test that the postgres service defines a healthcheck."""
    healthcheck = postgres_service.get("healthcheck", {})
    assert "pg_isready" in str(healthcheck.get("test", "")), "Healthcheck should use pg_isready"


def test_postgres_persists_data(postgres_service: dict[str, Any]) -> None:
    """Test that database data survives container restarts."""
    volumes = postgres_service.get("volumes", [])
    assert any("/var/lib/postgresql/data" in str(v) for v in volumes), (
        "Postgres data directory should be volume-mounted"
    )


def test_postgres_exposes_port(postgres_service: dict[str, Any]) -> None:
    """Test that postgres is reachable from the host."""
    ports = postgres_service.get("ports", [])
    assert any("5432" in str(p) for p in ports), "Port 5432 should be exposed"


def test_postgres_configures_credentials(postgres_service: dict[str, Any]) -> None:
    """Test that database credentials are configured via environment."""
    env = postgres_service.get("environment", {})
    env_text = str(env)
    for var in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
        assert var in env_text, f"Postgres service should set {var}"


def test_db_helper_scripts_exist_and_are_executable(repo_root: Path) -> None:
    """Test that database lifecycle scripts are present and runnable."""
    scripts_dir = repo_root / "scripts"
    for name in ("start-db.sh", "stop-db.sh", "reset-db.sh"):
        script = scripts_dir / name
        assert script.exists(), f"scripts/{name} should exist"
        assert os.access(script, os.X_OK), f"scripts/{name} should be executable"


def test_reset_script_requires_confirmation(repo_root: Path) -> None:
    """Test that the destructive reset script prompts before wiping data."""
    content = (repo_root / "scripts" / "reset-db.sh").read_text()
    assert "read" in content, "reset-db.sh should prompt for confirmation"


def test_env_example_documents_database_url(repo_root: Path) -> None:
    """Test that DATABASE_URL is documented for local setup."""
    env_example = (repo_root / ".env.example").read_text()
    assert "DATABASE_URL" in env_example
    assert "postgresql://" in env_example


def test_gitignore_excludes_local_db_artifacts(repo_root: Path) -> None:
    """Test that local database data and overrides stay untracked."""
    gitignore = (repo_root / ".gitignore").read_text()
    assert "postgres-data" in gitignore
    assert "docker-compose.override.yml" in gitignore


def test_readme_documents_database_setup(repo_root: Path) -> None:
    """Test that the README explains how to start the local database."""
    readme = (repo_root / "README.md").read_text()
    assert "docker-compose" in readme or "docker compose" in readme, (
        "README should document local database setup"
    )
