# ABOUTME: Tests for Docker build configuration (Step 7)
# ABOUTME: Validates Dockerfile structure, .dockerignore, and the CI docker build job

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def dockerfile(repo_root: Path) -> str:
    """Read the production Dockerfile."""
    path = repo_root / "Dockerfile"
    assert path.exists(), "Dockerfile should exist at the repo root"
    return path.read_text()


@pytest.fixture
def docker_job(repo_root: Path) -> dict[str, Any]:
    """Get the docker job from the CI workflow."""
    with open(repo_root / ".github" / "workflows" / "ci.yml") as f:
        workflow: dict[str, Any] = yaml.safe_load(f)
    assert "docker" in workflow["jobs"], "CI should have a 'docker' job"
    job: dict[str, Any] = workflow["jobs"]["docker"]
    return job


# --- Dockerfile ---


def test_dockerfile_is_multi_stage(dockerfile: str) -> None:
    """Test that the Dockerfile uses a multi-stage build."""
    from_lines = [line for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert len(from_lines) >= 2, "Dockerfile should be a multi-stage build"


def test_dockerfile_uses_pinned_uv_and_slim_python(dockerfile: str) -> None:
    """Test base images: pinned uv binary stage and slim Python runtime."""
    assert "ghcr.io/astral-sh/uv:" in dockerfile, "Should source uv from the official image"
    assert "ghcr.io/astral-sh/uv:latest" not in dockerfile, "uv image should be version-pinned"
    assert "python:3.12-slim" in dockerfile, "Runtime should be python:3.12-slim"


def test_dockerfile_layers_dependencies_before_source(dockerfile: str) -> None:
    """Test that dependency files are copied before src/ for layer caching."""
    assert "pyproject.toml" in dockerfile and "uv.lock" in dockerfile
    deps_idx = dockerfile.index("uv.lock")
    src_idx = dockerfile.index("COPY src/")
    assert deps_idx < src_idx, "Dependency files should be copied before application source"


def test_dockerfile_installs_locked_production_deps(dockerfile: str) -> None:
    """Test that dependencies install from the lockfile without dev extras."""
    assert "uv sync --locked" in dockerfile, "Should install from the lockfile"
    assert "--no-dev" in dockerfile, "Production image should not install dev dependencies"


def test_dockerfile_exposes_port_and_runs_uvicorn(dockerfile: str) -> None:
    """Test the runtime contract: port 8000, uvicorn entrypoint."""
    assert "EXPOSE 8000" in dockerfile
    assert "uvicorn" in dockerfile and "src.main:app" in dockerfile


def test_dockerignore_excludes_secrets_and_cruft(repo_root: Path) -> None:
    """Test that .dockerignore keeps secrets and non-runtime files out of the image."""
    path = repo_root / ".dockerignore"
    assert path.exists(), ".dockerignore should exist"
    content = path.read_text()
    for entry in (".env", "tests/", ".git", ".venv", "__pycache__"):
        assert entry in content, f".dockerignore should exclude {entry}"


# --- CI docker job ---


def test_docker_job_runs_after_quality_checks(docker_job: dict[str, Any]) -> None:
    """Test that images only build once tests pass."""
    needs = docker_job.get("needs", [])
    assert "test" in needs, "Docker build should require the test job"


def test_docker_job_has_registry_permissions(docker_job: dict[str, Any]) -> None:
    """Test that the job can push packages with the workflow token."""
    permissions = docker_job.get("permissions", {})
    assert permissions.get("packages") == "write", "Docker job needs packages: write"


def test_docker_job_scans_image_before_push(docker_job: dict[str, Any]) -> None:
    """Test that Trivy scans the built image with a safe pinned version."""
    steps = docker_job["steps"]
    trivy_steps = [s for s in steps if "aquasecurity/trivy-action" in s.get("uses", "")]
    assert trivy_steps, "Docker job should scan the image with Trivy"

    trivy = trivy_steps[0]
    # Versions <= 0.34.2 were affected by the 2026-03 supply-chain compromise
    version = trivy["uses"].split("@")[1]
    major, minor, *_ = (int(p) for p in version.lstrip("v").split("."))
    assert (major, minor) >= (0, 35), "Trivy action must be >= 0.35.0 (supply-chain incident)"

    with_args = trivy.get("with", {})
    assert "HIGH" in str(with_args.get("severity", "")), "Scan should cover HIGH severity"
    assert str(with_args.get("exit-code")) == "1", "Scan findings should fail the build"

    scan_idx = steps.index(trivy)
    push_steps = [s for s in steps if str(s.get("with", {}).get("push")) == "True"]
    for push_step in push_steps:
        assert steps.index(push_step) > scan_idx, "Image must be scanned before any push"


def test_docker_job_only_pushes_outside_prs(docker_job: dict[str, Any]) -> None:
    """Test that PR builds never push to the registry."""
    push_steps = [s for s in docker_job["steps"] if str(s.get("with", {}).get("push")) == "True"]
    assert push_steps, "Docker job should push images on branch builds"
    for step in push_steps:
        assert "pull_request" in str(step.get("if", "")), "Push must be gated off PR events"
