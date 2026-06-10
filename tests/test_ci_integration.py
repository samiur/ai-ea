# ABOUTME: Tests for CI test-execution configuration (Step 5)
# ABOUTME: Validates postgres service, coverage/JUnit reporting, artifacts, and CI environment

import importlib.util
import os
import socket
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
import yaml

IN_CI = os.environ.get("CI") == "true"


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def ci_workflow(repo_root: Path) -> dict[str, Any]:
    """Load the parsed CI workflow."""
    with open(repo_root / ".github" / "workflows" / "ci.yml") as f:
        workflow: dict[str, Any] = yaml.safe_load(f)
    return workflow


@pytest.fixture
def test_job(ci_workflow: dict[str, Any]) -> dict[str, Any]:
    """Get the test job from the CI workflow."""
    job: dict[str, Any] = ci_workflow["jobs"]["test"]
    return job


def _find_step(job: dict[str, Any], fragment: str) -> dict[str, Any] | None:
    """Find a job step whose 'uses' or 'run' contains the given fragment."""
    for step in job.get("steps", []):
        if fragment in step.get("uses", "") or fragment in step.get("run", ""):
            step_dict: dict[str, Any] = step
            return step_dict
    return None


# --- Workflow configuration ---


def test_test_job_has_postgres_service(test_job: dict[str, Any]) -> None:
    """Test that the test job runs a PostgreSQL service container."""
    services = test_job.get("services", {})
    assert "postgres" in services, "Test job should define a postgres service"

    postgres = services["postgres"]
    assert postgres["image"].startswith("postgres:15"), "Should use postgres:15"

    env = postgres.get("env", {})
    for var in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
        assert var in env, f"Postgres service should set {var}"

    options = postgres.get("options", "")
    assert "pg_isready" in options, "Postgres service should have a healthcheck"

    ports = postgres.get("ports", [])
    assert any("5432" in str(p) for p in ports), "Postgres should expose port 5432"


def test_test_job_sets_database_url(test_job: dict[str, Any]) -> None:
    """Test that the test job provides DATABASE_URL to the test run."""
    env = test_job.get("env", {})
    assert "DATABASE_URL" in env, "Test job should set DATABASE_URL"
    assert env["DATABASE_URL"].startswith("postgresql://"), (
        "DATABASE_URL should be a postgresql:// URL"
    )


def test_pytest_generates_junit_and_coverage(test_job: dict[str, Any]) -> None:
    """Test that pytest produces JUnit XML and coverage reports."""
    step = _find_step(test_job, "pytest")
    assert step is not None, "Test job should run pytest"

    run = step["run"]
    assert "--junitxml" in run, "pytest should generate a JUnit XML report"
    assert "--cov=src" in run, "pytest should measure coverage of src/"
    assert "--cov-report=xml" in run, "pytest should generate an XML coverage report"


def test_test_results_uploaded_as_artifacts(test_job: dict[str, Any]) -> None:
    """Test that JUnit and coverage reports are uploaded as artifacts."""
    upload_steps = [
        step
        for step in test_job.get("steps", [])
        if "actions/upload-artifact" in step.get("uses", "")
    ]
    assert upload_steps, "Test job should upload result artifacts"

    uploaded_paths = " ".join(str(step.get("with", {}).get("path", "")) for step in upload_steps)
    assert "junit.xml" in uploaded_paths, "junit.xml should be uploaded"
    assert "coverage.xml" in uploaded_paths, "coverage.xml should be uploaded"

    for step in upload_steps:
        assert step.get("if") == "always()", "Artifacts should upload even when tests fail"


def test_test_results_published_for_annotations(test_job: dict[str, Any]) -> None:
    """Test that test results are published to annotate PRs."""
    step = _find_step(test_job, "EnricoMi/publish-unit-test-result-action")
    assert step is not None, "Test job should publish test results for PR annotations"
    assert step.get("if") == "always()", "Results should publish even when tests fail"


def test_test_job_has_timeout(test_job: dict[str, Any]) -> None:
    """Test that the test job cannot hang CI indefinitely."""
    timeout = test_job.get("timeout-minutes")
    assert timeout is not None, "Test job should set timeout-minutes"
    assert timeout <= 15, "Test job timeout should be at most 15 minutes"


def test_individual_test_timeout_configured(repo_root: Path) -> None:
    """Test that a per-test timeout is configured via pytest-timeout."""
    with open(repo_root / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)

    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
    assert any(dep.startswith("pytest-timeout") for dep in dev_deps), (
        "pytest-timeout should be a dev dependency"
    )

    ini_options = pyproject["tool"]["pytest"]["ini_options"]
    assert "timeout" in ini_options, "A per-test timeout should be set in [tool.pytest.ini_options]"
    assert int(ini_options["timeout"]) <= 300, "Per-test timeout should be reasonable (<= 5 min)"


# --- CI environment ---


def test_required_test_dependencies_installed() -> None:
    """Test that the packages the suite relies on are importable."""
    for module in ("fastapi", "pydantic", "sqlmodel", "yaml", "pytest_cov", "pytest_timeout"):
        assert importlib.util.find_spec(module) is not None, (
            f"Required test dependency '{module}' is not installed"
        )


@pytest.mark.skipif(not IN_CI, reason="CI environment variables only set in CI")
def test_ci_environment_configured() -> None:
    """Test that the CI environment is configured as the workflow declares."""
    assert os.environ.get("CI") == "true"
    assert os.environ.get("DATABASE_URL", "").startswith("postgresql://"), (
        "DATABASE_URL should be set for the test job"
    )


@pytest.mark.skipif(
    not (IN_CI and os.environ.get("DATABASE_URL")),
    reason="Test database only provisioned in CI",
)
def test_database_service_reachable() -> None:
    """Test that the postgres service container accepts connections.

    Uses a plain TCP check: no database driver is a project dependency
    until Step 11 (SQLModel setup).
    """
    parsed = urlparse(os.environ["DATABASE_URL"])
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    with socket.create_connection((host, port), timeout=5):
        pass
