# ABOUTME: Tests for code quality tooling configuration (Step 6)
# ABOUTME: Validates ruff/mypy config, security scanning job, quality gate, and badges

import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def pyproject(repo_root: Path) -> dict[str, Any]:
    """Load the parsed pyproject.toml."""
    with open(repo_root / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


@pytest.fixture
def ci_workflow(repo_root: Path) -> dict[str, Any]:
    """Load the parsed CI workflow."""
    with open(repo_root / ".github" / "workflows" / "ci.yml") as f:
        workflow: dict[str, Any] = yaml.safe_load(f)
    return workflow


# --- Tool configuration ---


def test_ruff_configuration_valid(pyproject: dict[str, Any]) -> None:
    """Test that ruff is configured with the project's standards."""
    ruff = pyproject["tool"]["ruff"]
    assert ruff["target-version"] == "py312"
    assert ruff["line-length"] == 100

    lint = ruff["lint"]
    for ruleset in ("E", "F", "I", "B", "UP"):
        assert ruleset in lint["select"], f"Ruff should enable '{ruleset}' rules"


def test_mypy_configuration_valid(pyproject: dict[str, Any]) -> None:
    """Test that mypy is configured for strict-friendly checking."""
    mypy = pyproject["tool"]["mypy"]
    assert mypy["python_version"] == "3.12"
    assert mypy.get("warn_return_any") is True


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff binary not on PATH")
def test_all_files_pass_format_check(repo_root: Path) -> None:
    """Test that all Python files pass the ruff format check."""
    result = subprocess.run(
        ["ruff", "format", "--check", "src/", "tests/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Files need formatting:\n{result.stdout}{result.stderr}"


def test_security_tools_are_dev_dependencies(pyproject: dict[str, Any]) -> None:
    """Test that bandit and pip-audit are available for security scanning."""
    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
    for tool in ("bandit", "pip-audit"):
        assert any(dep.startswith(tool) for dep in dev_deps), f"'{tool}' should be a dev dependency"


# --- CI workflow ---


def test_ci_has_security_job(ci_workflow: dict[str, Any]) -> None:
    """Test that the CI pipeline includes a security scanning job."""
    jobs = ci_workflow["jobs"]
    assert "security" in jobs, "CI should have a 'security' job"

    runs = " ".join(step.get("run", "") for step in jobs["security"]["steps"])
    assert "bandit" in runs, "Security job should run bandit"
    assert "pip-audit" in runs, "Security job should run pip-audit"


def test_security_reports_uploaded(ci_workflow: dict[str, Any]) -> None:
    """Test that security scan reports are uploaded as artifacts."""
    security = ci_workflow["jobs"]["security"]
    upload_steps = [
        step for step in security["steps"] if "actions/upload-artifact" in step.get("uses", "")
    ]
    assert upload_steps, "Security job should upload scan reports"
    for step in upload_steps:
        assert step.get("if") == "always()", "Reports should upload even on failure"


def test_quality_gate_requires_all_checks(ci_workflow: dict[str, Any]) -> None:
    """Test that a single quality-gate job aggregates all required checks."""
    jobs = ci_workflow["jobs"]
    assert "quality-gate" in jobs, "CI should have a 'quality-gate' job"

    needs = jobs["quality-gate"]["needs"]
    for required in ("test", "lint", "type-check", "security"):
        assert required in needs, f"Quality gate should require '{required}'"


def test_quality_caches_configured(ci_workflow: dict[str, Any]) -> None:
    """Test that mypy/ruff caches are persisted between CI runs."""
    cached_paths = ""
    for job in ci_workflow["jobs"].values():
        for step in job.get("steps", []):
            if "actions/cache" in step.get("uses", ""):
                cached_paths += str(step.get("with", {}).get("path", ""))
    assert ".mypy_cache" in cached_paths, "mypy cache should be persisted"
    assert ".ruff_cache" in cached_paths, "ruff cache should be persisted"


def test_readme_has_quality_badges(repo_root: Path) -> None:
    """Test that the README shows CI and quality badges."""
    readme = (repo_root / "README.md").read_text()
    assert "badge" in readme, "README should contain status badges"
    for label in ("Ruff", "mypy"):
        assert label.lower() in readme.lower(), f"README should have a {label} badge"
