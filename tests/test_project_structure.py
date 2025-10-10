# ABOUTME: Tests to verify the project structure and setup
# ABOUTME: Validates that all required directories and files exist

import sys
from pathlib import Path

import pytest


@pytest.mark.unit
def test_src_directory_exists() -> None:
    """Test that the src/ directory exists."""
    src_dir = Path("src")
    assert src_dir.exists(), "src/ directory should exist"
    assert src_dir.is_dir(), "src/ should be a directory"


@pytest.mark.unit
def test_tests_directory_exists() -> None:
    """Test that the tests/ directory exists."""
    tests_dir = Path("tests")
    assert tests_dir.exists(), "tests/ directory should exist"
    assert tests_dir.is_dir(), "tests/ should be a directory"


@pytest.mark.unit
def test_src_init_file_exists() -> None:
    """Test that src/__init__.py exists."""
    init_file = Path("src/__init__.py")
    assert init_file.exists(), "src/__init__.py should exist"
    assert init_file.is_file(), "src/__init__.py should be a file"


@pytest.mark.unit
def test_src_main_file_exists() -> None:
    """Test that src/main.py exists."""
    main_file = Path("src/main.py")
    assert main_file.exists(), "src/main.py should exist"
    assert main_file.is_file(), "src/main.py should be a file"


@pytest.mark.unit
def test_tests_init_file_exists() -> None:
    """Test that tests/__init__.py exists."""
    init_file = Path("tests/__init__.py")
    assert init_file.exists(), "tests/__init__.py should exist"
    assert init_file.is_file(), "tests/__init__.py should be a file"


@pytest.mark.unit
def test_env_example_exists() -> None:
    """Test that .env.example exists."""
    env_example = Path(".env.example")
    assert env_example.exists(), ".env.example should exist"
    assert env_example.is_file(), ".env.example should be a file"


@pytest.mark.unit
def test_gitignore_exists() -> None:
    """Test that .gitignore exists."""
    gitignore = Path(".gitignore")
    assert gitignore.exists(), ".gitignore should exist"
    assert gitignore.is_file(), ".gitignore should be a file"


@pytest.mark.unit
def test_readme_exists() -> None:
    """Test that README.md exists and has content."""
    readme = Path("README.md")
    assert readme.exists(), "README.md should exist"
    assert readme.is_file(), "README.md should be a file"
    content = readme.read_text()
    assert len(content) > 0, "README.md should have content"
    assert "AI Executive Assistant" in content, "README.md should contain project name"


@pytest.mark.unit
def test_pyproject_toml_exists() -> None:
    """Test that pyproject.toml exists and has required fields."""
    pyproject = Path("pyproject.toml")
    assert pyproject.exists(), "pyproject.toml should exist"
    assert pyproject.is_file(), "pyproject.toml should be a file"
    content = pyproject.read_text()
    assert 'name = "ai-ea"' in content, "pyproject.toml should have project name"
    assert 'requires-python = ">=3.12"' in content, "Should require Python 3.12+"
    assert "fastapi" in content, "Should include FastAPI dependency"
    assert "pytest" in content, "Should include pytest dependency"


@pytest.mark.unit
def test_python_version() -> None:
    """Test that Python version is 3.12 or higher."""
    assert sys.version_info >= (3, 12), "Python version should be 3.12 or higher"


@pytest.mark.unit
def test_python_version_file_exists() -> None:
    """Test that .python-version file exists with correct version."""
    python_version_file = Path(".python-version")
    assert python_version_file.exists(), ".python-version should exist"
    content = python_version_file.read_text().strip()
    major, minor = content.split(".")[:2]
    assert int(major) == 3, "Major version should be 3"
    assert int(minor) >= 12, "Minor version should be 12 or higher"
