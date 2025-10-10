# Development Workflow Guide

## Overview

This guide explains the day-to-day development workflow for the AI Executive Assistant project, emphasizing our **TDD-first** and **CI/CD-automated** approach.

## Quick Start for New Contributors

```bash
# 1. Clone and setup
git clone <repo-url>
cd ai-ea
uv sync

# 2. Start local database
docker-compose up -d

# 3. Run tests to verify setup
uv run pytest

# 4. Start coding! (Always write tests first)
```

## Core Principles

### 1. Test-Driven Development (TDD)

**Every feature follows this cycle**:

```
RED → GREEN → REFACTOR → REPEAT
```

#### Red Phase: Write Failing Tests
```bash
# Create test file first
touch tests/test_new_feature.py

# Write your test
# tests/test_new_feature.py
def test_new_feature():
    result = new_feature()
    assert result == expected_value
```

Run test - it should fail:
```bash
uv run pytest tests/test_new_feature.py -v
# ❌ FAILED - function doesn't exist yet
```

#### Green Phase: Minimal Implementation
```python
# src/new_feature.py
def new_feature():
    return expected_value  # Simplest thing that could work
```

Run test - it should pass:
```bash
uv run pytest tests/test_new_feature.py -v
# ✅ PASSED
```

#### Refactor Phase: Clean Up
- Improve code structure
- Extract functions
- Improve names
- Add type hints
- Keep tests green!

### 2. CI/CD Integration

**Every push automatically triggers**:

1. **Tests** (pytest with coverage)
2. **Linting** (ruff check)
3. **Type Checking** (mypy --strict)
4. **Security Scanning** (bandit, pip-audit)
5. **Docker Build** (validates containerization)

You can run these locally before pushing:

```bash
# Full local quality check
./scripts/quality-check.sh

# Or manually:
uv run pytest --cov=src --cov-report=term
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ --strict
```

## Daily Workflow

### Starting a New Feature

1. **Check the plan**:
   ```bash
   # See what step you're implementing
   cat plan.md | grep "### Step"
   cat todo.md  # Check current phase
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/step-XX-feature-name
   ```

3. **Write tests first**:
   ```python
   # tests/test_feature.py
   def test_feature_does_something():
       """Test that feature does X when Y."""
       # Arrange
       setup = create_test_setup()

       # Act
       result = feature.do_something(setup)

       # Assert
       assert result.status == "success"
       assert result.data == expected_data
   ```

4. **Run tests (should fail)**:
   ```bash
   uv run pytest tests/test_feature.py -v
   ```

5. **Implement feature**:
   ```python
   # src/feature.py
   # ABOUTME: Implements feature X for use case Y
   # ABOUTME: Related to Step XX in plan.md

   from typing import Annotated
   from pydantic import Field

   def do_something(setup: Setup) -> Result:
       """Minimal implementation to pass test."""
       # Implementation here
       return Result(status="success", data=expected_data)
   ```

6. **Run tests (should pass)**:
   ```bash
   uv run pytest tests/test_feature.py -v
   ```

7. **Run full test suite**:
   ```bash
   uv run pytest
   ```

8. **Check code quality locally**:
   ```bash
   uv run ruff check .
   uv run ruff format .
   uv run mypy src/
   ```

9. **Commit with conventional commits**:
   ```bash
   git add .
   git commit -m "feat: implement feature X for step XX

   - Add Feature class with do_something method
   - Add comprehensive tests for feature behavior
   - Update documentation

   Relates to Step XX in plan.md"
   ```

10. **Push and create PR**:
    ```bash
    git push -u origin feature/step-XX-feature-name

    # Create PR via GitHub CLI
    gh pr create --title "Step XX: Feature Name" \
                 --body "Implements Step XX from plan.md

    ## Changes
    - Implemented feature X
    - Added tests
    - Updated docs

    ## Testing
    - [x] All tests pass
    - [x] Type checking passes
    - [x] Linting passes

    ## Checklist
    - [x] Tests written first (TDD)
    - [x] Documentation updated
    - [x] No breaking changes"
    ```

### Working on a Step

Each step in `plan.md` includes:
- What to test
- What to implement
- What to integrate

**Follow the step prompt exactly**:

```bash
# Example: Step 5 (Settings and Configuration)
# From plan.md:

# 1. Write tests in tests/test_config.py ✓
# 2. Create src/config.py ✓
# 3. Create .env.example ✓
# 4. Update main.py ✓
# 5. Add settings validation ✓
```

Check off each sub-task as you complete it.

## Code Quality Standards

### Type Annotations (Required)

```python
# ✅ Good - Modern type hints
def process_event(event: Event) -> Result | None:
    ...

# ❌ Bad - Old style Optional
from typing import Optional
def process_event(event: Event) -> Optional[Result]:
    ...
```

### Pydantic Models (Required pattern)

```python
# ✅ Good - Annotated with Field
from typing import Annotated
from pydantic import BaseModel, Field

class User(BaseModel):
    email: Annotated[str, Field(description="User email")]
    age: Annotated[int, Field(ge=0, le=150)] = 0

# ❌ Bad - Field in type position
class User(BaseModel):
    email: str = Field(description="User email")
    age: int = Field(ge=0, le=150, default=0)
```

### File Headers (Required)

```python
# ABOUTME: This module handles user authentication
# ABOUTME: Implements OAuth flows for Google and Slack

from typing import Annotated
...
```

### Async-First (Required for I/O)

```python
# ✅ Good - Async database operations
async def get_user(user_id: UUID) -> User | None:
    async with get_session() as session:
        result = await session.get(User, user_id)
        return result

# ❌ Bad - Blocking I/O
def get_user(user_id: UUID) -> User | None:
    session = get_session()
    return session.query(User).filter(User.id == user_id).first()
```

## Testing Patterns

### Unit Tests

```python
# tests/unit/test_scheduler.py
import pytest
from src.services.scheduler import Scheduler

def test_find_available_slots_returns_correct_count():
    """Test that slot finder returns requested number of slots."""
    scheduler = Scheduler()

    slots = scheduler.find_available_slots(
        duration_minutes=30,
        count=3,
        start_date="2025-01-15"
    )

    assert len(slots) == 3
    assert all(slot.duration_minutes == 30 for slot in slots)
```

### Integration Tests

```python
# tests/integration/test_calendar_sync.py
import pytest
from src.services.calendar_service import CalendarService
from src.integrations.google.calendar import GoogleCalendarClient

@pytest.mark.integration
async def test_sync_events_from_google_calendar(test_db, mock_google_creds):
    """Test full calendar sync flow."""
    service = CalendarService(test_db)

    # This actually calls Google API (mocked in tests)
    events = await service.sync_events(
        user_id=test_user.id,
        start_date="2025-01-01"
    )

    assert len(events) > 0
    assert all(e.calendar_id is not None for e in events)
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlmodel import create_engine, Session

@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_user(test_db):
    """Create test user."""
    user = User(email="test@example.com", timezone="UTC")
    test_db.add(user)
    test_db.commit()
    return user
```

## Git Workflow

### Branch Naming

```
feature/step-XX-short-description
bugfix/issue-number-description
hotfix/critical-issue-description
```

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
# Feature
git commit -m "feat(scheduler): add slot finding algorithm

Implements intelligent slot finding with constraint satisfaction
for multi-attendee meetings.

Relates to Step 28 in plan.md"

# Bug fix
git commit -m "fix(auth): handle token expiry correctly

Previously tokens weren't being refreshed, causing auth failures.
Now checks expiry before each request and refreshes if needed.

Fixes #42"

# Documentation
git commit -m "docs: update CI/CD overview with new steps"
```

### Pull Request Process

1. **Create PR** with clear title and description
2. **CI runs automatically** - all checks must pass
3. **Request review** from team
4. **Address feedback** in new commits
5. **Squash and merge** when approved

**PR Template**:
```markdown
## Description
Brief description of changes

## Related Step
Step XX: Feature Name (from plan.md)

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Refactoring

## Testing
- [ ] Tests written first (TDD)
- [ ] All tests passing
- [ ] Type checking passing
- [ ] Linting passing

## Checklist
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Follows step-by-step plan
```

## Common Tasks

### Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/test_scheduler.py

# Specific test
uv run pytest tests/test_scheduler.py::test_find_slots

# With coverage
uv run pytest --cov=src --cov-report=html

# Watch mode (requires pytest-watch)
uv run ptw
```

### Type Checking

```bash
# Full strict check
uv run mypy src/ --strict

# Check specific file
uv run mypy src/services/scheduler.py

# With cache
uv run mypy src/ --strict --cache-fine-grained
```

### Linting and Formatting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check formatting without changing
uv run ruff format --check .
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "add user table"

# Run migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Check current version
uv run alembic current
```

### Running the Development Server

```bash
# Standard
uv run uvicorn src.main:app --reload

# Custom port
uv run uvicorn src.main:app --reload --port 8001

# Debug mode
DEBUG=true uv run uvicorn src.main:app --reload
```

## Troubleshooting

### Tests Failing Locally But Passing in CI

Check environment variables:
```bash
# Copy example env
cp .env.example .env

# Ensure database is running
docker-compose ps

# Reset database
docker-compose down -v
docker-compose up -d
```

### Type Checking Errors

```bash
# Clear mypy cache
rm -rf .mypy_cache

# Reinstall stubs
uv add --dev types-python-jose types-passlib
```

### Import Errors

```bash
# Reinstall dependencies
uv sync

# Check Python path
uv run python -c "import sys; print(sys.path)"
```

## Resources

- **[plan.md](../plan.md)**: Complete implementation plan
- **[todo.md](../todo.md)**: Current progress
- **[CLAUDE.md](../CLAUDE.md)**: Working with AI assistant
- **[PRD.md](./PRD.md)**: Product requirements
- **[TRD.md](./TRD.md)**: Technical design
- **[cicd-overview.md](./cicd-overview.md)**: CI/CD documentation

## Getting Help

1. **Check documentation** - Most questions answered in plan.md or TRD.md
2. **Read error messages** - CI provides detailed failure information
3. **Ask in PR comments** - Team can provide context
4. **Create issue** - For bugs or unclear requirements

---

**Remember**: Test first, commit often, let CI do the heavy lifting!
