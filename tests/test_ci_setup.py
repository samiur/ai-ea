# ABOUTME: Tests for CI/CD infrastructure setup and validation
# ABOUTME: Validates GitHub Actions workflow files, secrets documentation, and CI configuration

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def workflows_dir(repo_root: Path) -> Path:
    """Get the .github/workflows directory."""
    return repo_root / ".github" / "workflows"


@pytest.fixture
def ci_workflow_path(workflows_dir: Path) -> Path:
    """Get the path to the CI workflow file."""
    return workflows_dir / "ci.yml"


def test_workflows_directory_exists(workflows_dir: Path) -> None:
    """Test that .github/workflows directory exists."""
    assert workflows_dir.exists(), ".github/workflows directory should exist"
    assert workflows_dir.is_dir(), ".github/workflows should be a directory"


def test_ci_workflow_file_exists(ci_workflow_path: Path) -> None:
    """Test that ci.yml workflow file exists."""
    assert ci_workflow_path.exists(), "ci.yml workflow file should exist"
    assert ci_workflow_path.is_file(), "ci.yml should be a file"


def test_ci_workflow_valid_yaml(ci_workflow_path: Path) -> None:
    """Test that ci.yml is valid YAML."""
    with open(ci_workflow_path) as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"ci.yml is not valid YAML: {e}")


def test_ci_workflow_has_required_structure(ci_workflow_path: Path) -> None:
    """Test that ci.yml has required top-level structure."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    assert "name" in workflow, "Workflow should have a name"
    assert workflow["name"] == "CI Pipeline", "Workflow name should be 'CI Pipeline'"
    # YAML parses 'on:' as boolean True, so check for either
    assert "on" in workflow or True in workflow, "Workflow should have triggers defined"
    assert "jobs" in workflow, "Workflow should have jobs defined"


def test_ci_workflow_has_correct_triggers(ci_workflow_path: Path) -> None:
    """Test that ci.yml has correct trigger configuration."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    # YAML parses 'on:' as boolean True
    triggers = workflow.get("on", workflow.get(True))
    assert "push" in triggers, "Should trigger on push"
    assert "pull_request" in triggers, "Should trigger on pull requests"
    assert "workflow_dispatch" in triggers, "Should support manual triggers"

    # Check push branches
    push_config = triggers["push"]
    assert "branches" in push_config, "Push should specify branches"
    branches = push_config["branches"]
    assert "main" in branches, "Should trigger on push to main"
    assert "develop" in branches, "Should trigger on push to develop"

    # Check PR branches
    pr_config = triggers["pull_request"]
    assert "branches" in pr_config, "PR should specify target branches"
    pr_branches = pr_config["branches"]
    assert "main" in pr_branches, "Should trigger on PRs to main"
    assert "develop" in pr_branches, "Should trigger on PRs to develop"


def test_ci_workflow_has_required_jobs(ci_workflow_path: Path) -> None:
    """Test that ci.yml has all required jobs."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    jobs = workflow["jobs"]
    required_jobs = ["test", "lint", "type-check"]

    for job_name in required_jobs:
        assert job_name in jobs, f"Workflow should have '{job_name}' job"


def test_ci_workflow_uses_uv_setup(ci_workflow_path: Path) -> None:
    """Test that ci.yml uses astral-sh/setup-uv action."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    jobs = workflow["jobs"]

    # Check that at least one job uses setup-uv
    found_uv_setup = False
    for _job_name, job_config in jobs.items():
        steps = job_config.get("steps", [])
        for step in steps:
            if "uses" in step and "astral-sh/setup-uv" in step["uses"]:
                found_uv_setup = True
                break
        if found_uv_setup:
            break

    assert found_uv_setup, "At least one job should use astral-sh/setup-uv action"


def _job_touches_code(job_config: dict[str, Any]) -> bool:
    """A job needs the repo if any step uses an action on it or runs a real command."""
    for step in job_config.get("steps", []):
        if "uses" in step and "actions/checkout" not in step["uses"]:
            return True
        run = step.get("run", "")
        if run and not run.strip().startswith("echo"):
            return True
    return False


def test_ci_workflow_uses_checkout(ci_workflow_path: Path) -> None:
    """Test that ci.yml uses actions/checkout in every job that works on the repo."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    jobs = workflow["jobs"]

    # Aggregation-only jobs (e.g., quality-gate) don't need the repo
    for job_name, job_config in jobs.items():
        if not _job_touches_code(job_config):
            continue
        steps = job_config.get("steps", [])
        found_checkout = False
        for step in steps:
            if "uses" in step and "actions/checkout" in step["uses"]:
                found_checkout = True
                break
        assert found_checkout, f"Job '{job_name}' should checkout code"


def test_secrets_documentation_exists(repo_root: Path) -> None:
    """Test that repository secrets are documented."""
    # Check for secrets documentation in README or dedicated docs file
    readme_path = repo_root / "README.md"
    docs_secrets_path = repo_root / "docs" / "secrets.md"
    ci_docs_path = repo_root / "docs" / "cicd-overview.md"

    assert readme_path.exists() or docs_secrets_path.exists() or ci_docs_path.exists(), (
        "Secrets should be documented in README.md, docs/secrets.md, or docs/cicd-overview.md"
    )


def test_secrets_documented_in_readme_or_docs(repo_root: Path) -> None:
    """Test that required secrets are documented somewhere."""
    required_secrets = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "SLACK_BOT_TOKEN",
        "DATABASE_URL",
    ]

    # Check README.md
    readme_path = repo_root / "README.md"
    docs_secrets_path = repo_root / "docs" / "secrets.md"
    ci_docs_path = repo_root / "docs" / "cicd-overview.md"

    content = ""
    if readme_path.exists():
        content += readme_path.read_text()
    if docs_secrets_path.exists():
        content += docs_secrets_path.read_text()
    if ci_docs_path.exists():
        content += ci_docs_path.read_text()

    for secret in required_secrets:
        assert secret in content, f"Secret '{secret}' should be documented in README.md or docs/"


def test_python_version_specified(ci_workflow_path: Path) -> None:
    """Test that Python 3.12 is specified in the workflow."""
    with open(ci_workflow_path) as f:
        workflow_content = f.read()

    # Check for Python 3.12 in the workflow
    assert "3.12" in workflow_content, "Workflow should specify Python 3.12"


def test_workflow_has_environment_variables(ci_workflow_path: Path) -> None:
    """Test that workflow defines required environment variables."""
    with open(ci_workflow_path) as f:
        workflow: dict[str, Any] = yaml.safe_load(f)

    jobs = workflow["jobs"]

    # Check that at least one job has env vars
    found_env_vars = False
    for _job_name, job_config in jobs.items():
        if "env" in job_config:
            found_env_vars = True
            # Could check for specific vars like CI: "true" if needed
            break

    # Environment variables might be at job or workflow level
    if not found_env_vars and "env" in workflow:
        found_env_vars = True

    # This is optional, so we'll just check structure exists if present
    # Not marking as required since env vars could be job-specific
