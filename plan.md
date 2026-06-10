# AI Executive Assistant - Implementation Plan

## Project Overview
Building an AI-powered executive assistant for calendar management and coordination, focusing on:
- Automatic rescheduling of 1-1s based on priority conflicts
- Finding time for new meetings across Google Calendar, Gmail, and Slack
- Policy-driven decision making with approval workflows
- Learning preferences via Zep memory graph (MVP scope per PRD 2026-06-10)

**Architecture (PRD §7, decided 2026-06-10): hybrid agent + deterministic core.**
An LLM agent (Claude Agent SDK) handles parsing, drafting, and coordination
through MCP tools; all calendar **writes** go through a thin deterministic
Scheduler service that owns two-phase commit, idempotency, and policy checks.
Where mature MCP servers exist (Calendar, Gmail, Slack), we use them instead
of hand-building API clients.

## Technical Stack
- **Backend**: Python with FastAPI
- **Agent**: Claude Agent SDK + MCP servers (Calendar/Gmail/Slack); model configurable in settings, defaulting to the latest Claude model
- **Database**: PostgreSQL with SQLModel ORM
- **Queue**: Redis with RQ
- **Memory**: Zep for preference learning (MVP)
- **Integrations**: MCP servers for reads/comms; google-api-python-client for calendar writes only
- **Testing**: Pytest, Playwright for integration tests
- **Package Management**: uv

## Implementation Phases

> **Note**: CI/CD infrastructure (Steps 4-8) was moved early in the plan to provide immediate quality feedback and automated testing from the start. See `docs/step-reorganization.md` for details.
>
> **Revision 2026-06-10**: Step prompts renumbered to match the reorganized scheme used by `todo.md` (previously only the phase overview had been updated). Steps 21-35 rewritten for the hybrid agent+MCP architecture and Zep-in-MVP (PRD changelog 2026-06-10).

### Phase 1: Foundation & CI/CD (Steps 1-10)
Basic project setup, **CI/CD pipeline** (Steps 4-8), database, and API structure

### Phase 2: Database & Models (Steps 11-17)
Database setup, core models, repository pattern, and feature flags

### Phase 3: Authentication & Security (Steps 18-20)
OAuth configuration, secure token storage, and JWT middleware

### Phase 4: Calendar Core (Steps 21-25)
Google OAuth, calendar reads via MCP, availability math, deterministic write service, conflict detection

### Phase 5: Agent & Communication (Steps 26-32)
Agent foundation, Gmail/Slack via MCP, structured-output parsing, approval cards, drafting, Zep memory

### Phase 6: Orchestration (Steps 33-35)
Slot finder, approval workflow + decision logger + shadow scorer, orchestrator with shadow mode

---

## Implementation Prompts

### Step 1: Project Initialization

```text
Initialize a new Python project for an AI Executive Assistant using uv.

Requirements:
1. Create a new directory called 'ai-executive-assistant'
2. Initialize with uv (uv init)
3. Set Python version to 3.12
4. Add these initial dependencies:
   - fastapi
   - uvicorn[standard]
   - pydantic
   - pydantic-settings
   - sqlmodel
   - alembic
   - httpx
   - pytest
   - pytest-asyncio
   - mypy
   - ruff

5. Create basic project structure:
   - src/
     - __init__.py
     - main.py (empty for now)
   - tests/
     - __init__.py
   - .env.example
   - .gitignore (include .env, __pycache__, .venv, etc.)
   - README.md with project description

6. Configure pyproject.toml with:
   - Proper project metadata
   - Python 3.12 requirement
   - Dev dependencies group for testing tools
   - Scripts section for common commands

Follow TDD: Write a test first that verifies the project structure exists.
```

### Step 2: Basic FastAPI Application

```text
Create a basic FastAPI application with health and status endpoints.

Building on Step 1, implement:

1. First write tests in tests/test_main.py:
   - Test that GET /health returns 200 with {"status": "healthy"}
   - Test that GET /status returns app version and environment
   - Test that root path returns API documentation link

2. Then implement in src/main.py:
   - Create FastAPI app instance
   - Add /health endpoint returning {"status": "healthy"}
   - Add /status endpoint with version from pyproject.toml
   - Add root welcome endpoint
   - Include proper CORS middleware for localhost development
   - Add request ID middleware for tracing

3. Create src/api/__init__.py and src/api/routes/__init__.py for route organization

4. Update pyproject.toml with a dev script to run:
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

Ensure all tests pass before moving forward.
```

### Step 3: Settings and Configuration

```text
Implement Pydantic settings management with environment variables.

Building on Steps 1-2:

1. Write tests in tests/test_config.py:
   - Test loading settings from environment variables
   - Test validation of required fields
   - Test default values
   - Test settings singleton pattern

2. Create src/config.py with Settings class:
   - Use pydantic-settings BaseSettings
   - Define fields:
     - app_name: str = "AI Executive Assistant"
     - version: str (from pyproject.toml)
     - environment: Literal["development", "staging", "production"]
     - debug: bool
     - database_url: str
     - redis_url: str
     - secret_key: str (for JWT)
     - google_client_id: Optional[str]
     - google_client_secret: Optional[str]
     - slack_bot_token: Optional[str]
     - slack_signing_secret: Optional[str]
   - Use Annotated[Type, Field(...)] pattern
   - Load from .env file

3. Create .env.example with all variables documented

4. Update main.py to use settings:
   - Import and instantiate settings
   - Add settings info to /status endpoint
   - Redact sensitive values in responses

5. Add settings validation on startup

Ensure settings are properly loaded and validated.
```

### Step 4: Basic GitHub Actions Workflow

```text
Set up foundational GitHub Actions workflow for CI/CD.

Building on Steps 1-3:

1. Write tests in tests/test_ci_setup.py:
   - Test that workflow files are valid YAML
   - Test that required secrets are documented
   - Test that workflow triggers are configured correctly

2. Create .github/workflows/ci.yml:
   - Workflow name: "CI Pipeline"
   - Triggers:
     - push to main and develop branches
     - pull requests to main and develop
     - workflow_dispatch (manual trigger)
   - Basic structure with jobs:
     - test
     - lint
     - type-check

3. Configure checkout and Python setup:
   - actions/checkout@v4 for code
   - astral-sh/setup-uv@v5 for uv installation
   - Cache uv dependencies for faster runs
   - Set up Python 3.12 using uv python install

4. Define environment variables:
   - PYTHON_VERSION: "3.12"
   - UV_SYSTEM_PYTHON: "1"
   - CI: "true"

5. Create job matrix for Python versions:
   - Test on Python 3.12 (primary)
   - Optional: Add 3.11 for compatibility testing

6. Add basic status badges to README.md:
   - CI status badge
   - Test coverage badge (setup for later)

7. Document required repository secrets:
   - GOOGLE_CLIENT_ID (for integration tests)
   - GOOGLE_CLIENT_SECRET
   - SLACK_BOT_TOKEN
   - DATABASE_URL (test database)

Ensure workflow runs successfully on push.
```

### Step 5: Test Execution in CI

```text
Implement comprehensive test execution in GitHub Actions.

Building on Steps 1-4:

1. Write tests in tests/test_ci_integration.py:
   - Test that CI environment is properly configured
   - Test that all required dependencies are installed
   - Test that test database is accessible

2. Enhance the test job in .github/workflows/ci.yml:
   - Install project dependencies:
     - uv sync --locked
   - Install test dependencies:
     - uv sync --group dev
   - Set up test database service:
     - Use postgres:15 service container
     - Configure healthcheck
     - Set DATABASE_URL environment variable

3. Add PostgreSQL service to workflow:
   ```yaml
   services:
     postgres:
       image: postgres:15
       env:
         POSTGRES_USER: test_user
         POSTGRES_PASSWORD: test_pass
         POSTGRES_DB: test_db
       options: >-
         --health-cmd pg_isready
         --health-interval 10s
         --health-timeout 5s
         --health-retries 5
       ports:
         - 5432:5432
   ```

4. Configure test execution:
   - Run: uv run pytest tests/ -v --tb=short
   - Generate JUnit XML report: --junitxml=junit.xml
   - Generate coverage report: --cov=src --cov-report=xml
   - Continue on error for coverage reporting

5. Upload test results:
   - actions/upload-artifact for test reports
   - Store junit.xml for test reporting
   - Store coverage.xml for coverage tracking

6. Add test result annotations:
   - Use EnricoMi/publish-unit-test-result-action
   - Annotate PR with test failures
   - Show test trends over time

7. Configure test timeout:
   - Set job timeout: 15 minutes
   - Set individual test timeout in pytest.ini

Test that all tests run successfully in CI environment.
```

### Step 6: Code Quality Checks

```text
Add comprehensive code quality checks to CI pipeline.

Building on Steps 1-5:

1. Write tests in tests/test_code_quality.py:
   - Test that ruff configuration is valid
   - Test that mypy configuration is valid
   - Test that all Python files pass formatting checks

2. Create lint job in .github/workflows/ci.yml:
   - Name: "Lint and Format Check"
   - Runs on: ubuntu-latest
   - Steps:
     - Checkout code
     - Setup uv and Python
     - Install dependencies (uv sync --locked)
     - Run ruff check: uv run ruff check src/ tests/
     - Run ruff format check: uv run ruff format --check src/ tests/

3. Create type-check job:
   - Name: "Type Checking"
   - Runs on: ubuntu-latest
   - Steps:
     - Checkout code
     - Setup uv and Python
     - Install dependencies
     - Run mypy: uv run mypy src/ --strict

4. Add security scanning:
   - Create security job
   - Use bandit for Python security linting:
     - uv add --dev bandit
     - uv run bandit -r src/ -f json -o bandit-report.json
   - Upload security scan results

5. Add dependency vulnerability scanning:
   - Use pip-audit:
     - uv add --dev pip-audit
     - uv run pip-audit --format json --output audit-report.json
   - Fail on high/critical vulnerabilities
   - Allow warnings to pass

6. Create combined quality gate:
   - All quality checks must pass
   - Block PR merge if any check fails
   - Add status check requirements in branch protection

7. Configure caching for speed:
   - Cache uv packages: ~/.cache/uv
   - Cache mypy cache: .mypy_cache/
   - Cache ruff cache: .ruff_cache/

8. Add quality badges to README:
   - Ruff badge
   - Type checking badge
   - Security scanning badge

Ensure all code quality checks pass on current codebase.
```

### Step 7: Docker Build and Registry

```text
Add Docker image building and registry push to CI/CD pipeline.

Building on Steps 1-6:

1. Write tests in tests/test_docker.py:
   - Test Dockerfile syntax validity
   - Test that all required files are copied
   - Test multi-stage build structure

2. Create production Dockerfile:
   ```dockerfile
   FROM ghcr.io/astral-sh/uv:0.7.4 AS uv
   FROM python:3.12-slim AS base

   # Copy uv binary
   COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

   # Set working directory
   WORKDIR /app

   # Copy dependency files
   COPY pyproject.toml uv.lock ./

   # Install dependencies
   RUN uv sync --locked --no-dev

   # Copy application
   COPY src/ ./src/
   # (alembic/ + alembic.ini arrive in Step 14 — add those COPY lines then)

   # Expose port
   EXPOSE 8000

   # Run app
   CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. Create .dockerignore:
   - .git/
   - .github/
   - tests/
   - *.md
   - .env
   - .venv/
   - __pycache__/
   - *.pyc

4. Add Docker build job to .github/workflows/ci.yml:
   - Name: "Build Docker Image"
   - Runs after test job passes
   - Steps:
     - Checkout code
     - Set up Docker Buildx
     - Login to GitHub Container Registry
     - Extract metadata for tags
     - Build and push image

5. Configure Docker tags strategy:
   - Latest: for main branch
   - Branch name: for feature branches
   - PR number: for pull requests
   - SHA: for all commits
   - Semantic version: for tags

6. Use Docker layer caching:
   - actions/cache for Docker layers
   - Cache key based on Dockerfile and dependencies
   - Restore from previous builds

7. Add image security scanning:
   - Use Trivy for vulnerability scanning
   - aquasecurity/trivy-action
   - Scan built image before push
   - Upload scan results to GitHub Security

8. Configure GitHub Container Registry:
   - Use ghcr.io/[username]/ai-executive-assistant
   - Set package visibility (private initially)
   - Configure retention policy
   - Add package description and README

9. Add build matrix for platforms:
   - linux/amd64
   - linux/arm64 (optional)

Test Docker build locally and in CI.
```

### Step 8: Deployment Automation

```text
Implement automated deployment workflows for staging and production.

Building on Steps 1-7:

1. Create .github/workflows/deploy-staging.yml:
   - Triggers:
     - Push to develop branch
     - Manual workflow_dispatch
   - Jobs:
     - deploy-staging
   - Environment: staging
   - Required approvals: 0 (auto-deploy)

2. Create .github/workflows/deploy-production.yml:
   - Triggers:
     - Push to main branch (tags only)
     - Manual workflow_dispatch
   - Jobs:
     - deploy-production
   - Environment: production
   - Required approvals: 1 (manual approval)

3. Configure GitHub Environments:
   - staging environment:
     - No protection rules
     - Environment secrets
     - Environment variables
   - production environment:
     - Required reviewers: [team leads]
     - Deployment branches: main only
     - Environment secrets
     - Environment variables

4. Add deployment job structure:
   ```yaml
   deploy:
     runs-on: ubuntu-latest
     environment:
       name: staging
       url: https://staging.example.com
     steps:
       - Checkout code
       - Download Docker image
       - Deploy to platform
       - Run health checks
       - Notify on success/failure
   ```

5. Implement health check verification:
   - Wait for deployment to complete
   - Check /health endpoint
   - Verify database connectivity
   - Verify external service connections
   - Rollback on failure

6. Add deployment notifications:
   - Slack notification on deployment start
   - Slack notification on success/failure
   - GitHub deployment status
   - Email notification for production

7. Create deployment scripts:
   - scripts/deploy.sh:
     - Pull latest image
     - Run database migrations
     - Restart services
     - Verify health
   - scripts/rollback.sh:
     - Revert to previous image
     - Rollback migrations if needed
     - Restore service

8. Configure deployment secrets:
   - Database credentials
   - API keys
   - OAuth secrets
   - Service URLs
   - Encryption keys

9. Add smoke tests post-deployment:
   - tests/smoke/ directory
   - Critical path testing
   - API endpoint availability
   - Database connectivity
   - External service integration

10. Document deployment process:
    - docs/deployment.md
    - Manual deployment steps
    - Rollback procedures
    - Troubleshooting guide
    - Emergency contacts

11. Set up deployment monitoring:
    - Track deployment frequency
    - Track deployment duration
    - Track failure rate
    - Alert on failed deployments

Test deployment workflow to staging environment.
```

### Step 9: Docker Compose for PostgreSQL

```text
Set up PostgreSQL with Docker Compose for local development.

Building on Steps 1-8:

1. Create docker-compose.yml with:
   - PostgreSQL 15 service
   - Proper volumes for data persistence
   - Health check configuration
   - Environment variables for database setup
   - Port 5432 exposed
   - Network configuration

2. Create docker-compose.override.yml for local dev overrides

3. Add database connection testing:
   - Write test in tests/test_database.py
   - Test that database is reachable
   - Test connection pool settings

4. Create scripts/ directory with:
   - start-db.sh: Start database container
   - stop-db.sh: Stop database container
   - reset-db.sh: Reset database (warning prompt)

5. Update .env.example with:
   DATABASE_URL=postgresql://assistant:assistant@localhost:5432/ai_assistant

6. Update README with database setup instructions

7. Add to .gitignore:
   - postgres-data/
   - docker-compose.override.yml

Verify database starts and is accessible.
```

### Step 10: API Error Handling and Responses

```text
Implement comprehensive error handling and standardized API responses.

Building on Steps 1-9:

1. Write tests in tests/test_error_handling.py:
   - Test various error scenarios
   - Test error response format
   - Test error logging
   - Test client error vs server error

2. Create src/api/errors.py:
   - Custom exception classes:
     - APIError(base)
     - NotFoundError(404)
     - ValidationError(400)
     - AuthenticationError(401)
     - AuthorizationError(403)
     - ConflictError(409)
     - ExternalServiceError(503)
   - Error response model

3. Create src/api/responses.py:
   - StandardResponse model:
     - success: bool
     - data: Optional[Any]
     - error: Optional[ErrorDetail]
     - request_id: str
     - timestamp: datetime
   - Pagination response model
   - Response factory functions

4. Create src/middleware/error_handler.py:
   - Global exception handler
   - Map exceptions to HTTP status codes
   - Log errors with context
   - Sanitize error messages for production

5. Update main.py:
   - Register error handlers
   - Add request context middleware
   - Implement request ID tracking

6. Create src/api/routes/health.py:
   - Move health endpoints to proper router
   - Add detailed health checks:
     - Database reachability (raw connection ping; ORM health lands in Step 11)
     - Redis connectivity (mock for now)
     - External service status

Ensure consistent error handling across all endpoints.
```

### Step 11: SQLModel Setup and Connection

```text
Configure SQLModel ORM and database connection management.

Building on Steps 1-10:

1. Write tests in tests/test_database.py:
   - Test database connection
   - Test session creation
   - Test connection pool configuration
   - Test async session management

2. Create src/database.py:
   - Import SQLModel and create_engine
   - Setup async engine with proper pool settings:
     - pool_size=5
     - max_overflow=10
     - pool_pre_ping=True (for connection health)
   - Create SessionLocal with proper typing
   - Implement get_session dependency for FastAPI
   - Add init_db() function for table creation

3. Create src/models/__init__.py and src/models/base.py:
   - Define BaseModel class inheriting from SQLModel
   - Add common fields:
     - id: UUID with default_factory
     - created_at: datetime with default_factory
     - updated_at: datetime with onupdate

4. Update main.py:
   - Add database initialization on startup
   - Add database health check to /health endpoint
   - Implement proper shutdown handling

5. Create tests/conftest.py:
   - Setup test database
   - Session fixtures for testing
   - Database cleanup between tests

Ensure all database operations are async and properly managed.
```

### Step 12: Person and Policy Data Models

```text
Create Person and Policy data models with full CRUD operations.

Building on Steps 1-11:

1. Write comprehensive tests in tests/test_models_person_policy.py:
   - Test Person model validation
   - Test Policy model validation
   - Test CRUD operations for both
   - Test relationships between models
   - Test timezone validation

2. Create src/models/person.py:
   - Person model with SQLModel:
     - person_id: UUID (primary key)
     - email: EmailStr (unique index)
     - display_name: str
     - timezone: str (validate with pytz)
     - is_active: bool = True
   - Add proper indexes and constraints

3. Create src/models/policy.py:
   - Policy model:
     - policy_id: UUID (primary key)
     - name: str (unique)
     - tier: Enum["VIP", "Customer", "Hiring", "Internal", "OneOnOne"]
       (canonical tier enum — PRD R2)
     - reschedule_window_days: int (validated 0-30)
     - buffer_before_min: int (validated 0-60)
     - buffer_after_min: int (validated 0-60)
     - working_hours: JSON field (dict structure)
     - strict_mode: bool = False
   - Add validation for working_hours structure

4. Create src/repositories/person.py:
   - PersonRepository with async methods:
     - create(person: Person)
     - get(person_id: UUID)
     - get_by_email(email: str)
     - update(person_id: UUID, updates: dict)
     - delete(person_id: UUID)
     - list(limit: int, offset: int)

5. Create src/repositories/policy.py:
   - Similar CRUD operations for Policy

Ensure all models have proper validation and relationships.
```

### Step 13: Meeting Series and Related Models

```text
Implement MeetingSeries and related scheduling models.

Building on Steps 1-12:

1. Write tests in tests/test_models_meetings.py:
   - Test MeetingSeries model validation
   - Test recurrence rule parsing
   - Test attendee relationships
   - Test series-policy associations

2. Create src/models/meeting.py:
   - MeetingSeries model:
     - series_id: UUID (primary key)
     - title: str
     - owner_id: UUID (FK to Person)
     - default_duration_min: int (15-480)
     - cadence_rule: str (iCal RRULE format)
     - policy_id: UUID (FK to Policy)
     - is_active: bool = True
   - MeetingAttendee join table:
     - series_id: UUID (FK)
     - person_id: UUID (FK)
     - is_required: bool
     - response_status: Enum

3. Create src/models/schedule.py:
   - ScheduleIntent model:
     - intent_id: UUID
     - kind: Enum["new", "reschedule", "cancel", "hold"]
     - series_id: Optional[UUID]
     - requested_by: UUID (FK to Person)
     - target_date: date
     - duration_min: int
     - status: Enum["pending", "approved", "rejected", "completed"]
     - source: Enum["slack", "email", "conflict_detector", "manual"]

4. Update repositories:
   - MeetingRepository with series CRUD
   - Attendee management methods
   - Query by owner or attendee

5. Create src/utils/rrule.py:
   - RRULE parser and validator
   - Next occurrence calculator
   - Series expansion utility

Validate all recurrence patterns and relationships.
```

### Step 14: Database Migrations with Alembic

```text
Set up Alembic for database migrations and create initial schema.

Building on Steps 1-13:

1. Write tests in tests/test_migrations.py:
   - Test migration up and down
   - Test migration ordering
   - Test schema consistency

2. Initialize Alembic:
   - Run: alembic init alembic
   - Configure alembic.ini:
     - Set sqlalchemy.url from environment
     - Configure naming convention
   - Update alembic/env.py:
     - Import all models
     - Use SQLModel metadata
     - Support async migrations

3. Create initial migration:
   - Generate migration for all current models
   - Review and adjust auto-generated migration
   - Add proper indexes and constraints
   - Include seed data migration for default policies

4. Create src/database/migrations.py:
   - run_migrations() function
   - check_migration_status()
   - rollback_migration()

5. Update main.py:
   - Auto-run migrations on startup in dev
   - Add /admin/migrations endpoint (dev only)

6. Create scripts/migrate.sh:
   - Wrapper for common migration commands
   - Include safety checks

7. Update the Dockerfile (Step 7) to COPY alembic/ and alembic.ini, and
   run migrations before app start

8. Document migration workflow in README

Ensure migrations work up and down cleanly.
```

### Step 15: Repository Pattern Implementation

```text
Implement a clean repository pattern for data access.

Building on Steps 1-14:

1. Write tests in tests/test_repositories.py:
   - Test base repository methods
   - Test query builder
   - Test pagination
   - Test transaction handling

2. Create src/repositories/base.py:
   - BaseRepository abstract class:
     - get(id: UUID) -> Optional[T]
     - list(limit, offset, filters) -> List[T]
     - create(item: T) -> T
     - update(id: UUID, updates: dict) -> T
     - delete(id: UUID) -> bool
     - exists(id: UUID) -> bool
   - Use generics for type safety
   - Implement common query patterns

3. Update existing repositories:
   - PersonRepository(BaseRepository[Person])
   - PolicyRepository(BaseRepository[Policy])
   - MeetingRepository(BaseRepository[MeetingSeries])
   - Add custom methods as needed

4. Create src/repositories/unit_of_work.py:
   - UnitOfWork pattern for transactions
   - Context manager for auto-rollback
   - Support for multiple repositories

5. Create src/api/dependencies.py:
   - get_person_repo() -> PersonRepository
   - get_policy_repo() -> PolicyRepository
   - get_uow() -> UnitOfWork
   - Proper dependency injection

6. Add repository usage examples in tests

Ensure clean separation between models and data access.
```

### Step 16: Feature Flags System

```text
Implement a feature flag system for gradual rollout and configuration.

Building on Steps 1-15:

1. Write tests in tests/test_feature_flags.py:
   - Test flag evaluation
   - Test flag overrides
   - Test user-specific flags
   - Test flag persistence

2. Create src/models/feature_flag.py:
   - FeatureFlag model:
     - flag_name: str (unique)
     - is_enabled: bool
     - rollout_percentage: int (0-100)
     - enabled_users: JSON (list of user IDs)
     - enabled_environments: JSON
     - metadata: JSON

3. Create src/services/feature_flags.py:
   - FeatureFlagService class:
     - is_enabled(flag_name, user_id=None)
     - get_all_flags()
     - update_flag(flag_name, updates)
     - evaluate_rollout(flag_name, user_id)
   - Cache flag values in memory
   - Support runtime updates

4. Define initial flags in src/config/features.py:
   - SHADOW_MODE (rollout Phase 0 — drafts + verdicts only, no sends/writes)
   - AUTO_RESCHEDULE_ONE_ON_ONE
   - SOFT_HOLDS_ENABLED
   - SLACK_INTEGRATION_ENABLED
   - GMAIL_INTEGRATION_ENABLED
   - TRAVEL_MODE_ENABLED
   - SANITY_SWEEPS_ENABLED

5. Create src/api/routes/admin.py:
   - GET /admin/features - list all flags
   - PUT /admin/features/{flag_name} - update flag
   - POST /admin/features/{flag_name}/evaluate - test evaluation

6. Add feature flag checks to settings initialization

Ensure flags can control feature availability dynamically.
```

### Step 17: Policy YAML Loader and Parser

```text
Create a system to load and parse policy configurations from YAML/JSON.

Building on Steps 1-16:

1. Write tests in tests/test_policy_loader.py:
   - Test YAML parsing
   - Test JSON parsing
   - Test policy validation
   - Test policy merging
   - Test invalid policy handling

2. Create policies/defaults.yaml:
   - Default policy configurations:
     ```yaml
     policies:
       one_on_one:
         tier: OneOnOne
         reschedule_window_days: 14
         buffer_before_min: 5
         buffer_after_min: 5
         working_hours:
           default: ["09:00", "17:00"]
       customer:
         tier: Customer
         reschedule_window_days: 7
         buffer_before_min: 15
         buffer_after_min: 10
     ```

3. Create src/services/policy_loader.py:
   - PolicyLoader class:
     - load_from_file(filepath)
     - load_from_string(content)
     - validate_policy(policy_dict)
     - merge_policies(base, override)
   - Support environment-specific overrides
   - Validate against schema

4. Create src/schemas/policy.py:
   - Pydantic models for policy validation:
     - PolicyConfig
     - WorkingHours
     - PolicySet
   - Custom validators for time ranges

5. Update PolicyRepository:
   - load_defaults() method
   - sync_from_config() method
   - Support for policy templates

6. Add CLI command for policy management:
   - scripts/manage-policies.py
   - Load, validate, and sync policies

Ensure policies can be managed via configuration files.
```

### Step 18: OAuth Configuration Models

```text
Design OAuth configuration models for Google and Slack integrations.

Building on Steps 1-17:

1. Write tests in tests/test_oauth_models.py:
   - Test OAuth credential models
   - Test token refresh logic
   - Test token expiry handling
   - Test scope validation

2. Create src/models/oauth.py:
   - OAuthCredential model:
     - credential_id: UUID
     - provider: Enum["google", "slack"]
     - user_id: UUID (FK to Person)
     - access_token: str (encrypted)
     - refresh_token: Optional[str] (encrypted)
     - token_expiry: datetime
     - scopes: JSON (list)
     - is_valid: bool
   - Add indexes for user+provider lookup

3. Create src/schemas/oauth.py:
   - OAuthConfig pydantic model
   - TokenResponse model
   - AuthorizationRequest model
   - Scope validation

4. Create src/services/encryption.py:
   - Simple encryption for tokens:
     - encrypt_token(token: str) -> str
     - decrypt_token(encrypted: str) -> str
   - Use Fernet symmetric encryption
   - Derive key from SECRET_KEY

5. Update settings:
   - Add OAuth URLs:
     - google_auth_uri
     - google_token_uri
     - slack_oauth_url
   - Add required scopes configuration

6. Create migration for oauth_credentials table

Ensure OAuth tokens are securely stored and managed.
```

### Step 19: Secure Token Storage

```text
Implement secure token storage with encryption and key management.

Building on Steps 1-18:

1. Write tests in tests/test_token_storage.py:
   - Test token encryption/decryption
   - Test token storage and retrieval
   - Test token rotation
   - Test key derivation

2. Create src/services/token_manager.py:
   - TokenManager class:
     - store_token(user_id, provider, tokens)
     - get_token(user_id, provider)
     - refresh_token(user_id, provider)
     - revoke_token(user_id, provider)
     - check_token_validity(user_id, provider)
   - Auto-refresh expired tokens
   - Handle refresh failures

3. Enhance encryption service:
   - Add key rotation support
   - Implement proper key derivation (PBKDF2)
   - Add encryption versioning
   - Support for different encryption levels

4. Create src/repositories/oauth.py:
   - OAuthRepository(BaseRepository):
     - get_valid_credential(user_id, provider)
     - store_credential(credential)
     - update_tokens(credential_id, tokens)
     - mark_invalid(credential_id)

5. Add token cleanup job:
   - Remove expired tokens
   - Alert on refresh failures
   - Log token usage

6. Create src/api/routes/auth.py:
   - GET /auth/status - check auth status
   - DELETE /auth/revoke/{provider} - revoke tokens

Ensure tokens are encrypted at rest and properly managed.
```

### Step 20: JWT Middleware for Internal APIs

```text
Implement JWT authentication middleware for internal API security.

Building on Steps 1-19:

1. Write tests in tests/test_jwt_auth.py:
   - Test JWT generation
   - Test JWT validation
   - Test expired token handling
   - Test invalid token handling
   - Test middleware integration

2. Create src/services/jwt_service.py:
   - JWTService class:
     - create_token(user_id, expires_delta)
     - verify_token(token) -> dict
     - refresh_token(token) -> str
     - get_current_user(token) -> Person
   - Use python-jose for JWT operations
   - Include proper claims (sub, exp, iat, jti)

3. Create src/middleware/authentication.py:
   - JWTAuthMiddleware class
   - Extract and validate bearer tokens
   - Set user context in request state
   - Handle authentication errors

4. Create src/api/dependencies/auth.py:
   - get_current_user() dependency
   - require_auth() dependency
   - optional_auth() dependency
   - admin_only() dependency

5. Create src/api/routes/auth_internal.py:
   - POST /auth/login - generate JWT
   - POST /auth/refresh - refresh JWT
   - GET /auth/me - get current user

6. Update API routes:
   - Add authentication to protected endpoints
   - Implement role-based access
   - Add auth documentation

Ensure all internal APIs are properly secured.
```

### Step 21: Google OAuth Credential Setup

```text
Implement Google OAuth flow for Calendar and Gmail access.

These credentials feed two consumers: the MCP servers used for reads and
comms (Steps 22, 27) and the deterministic Scheduler write client (Step 24).

Building on Steps 1-20:

1. Write tests in tests/test_google_oauth.py:
   - Test OAuth URL generation
   - Test callback handling
   - Test token exchange
   - Test scope validation

2. Create src/integrations/google/__init__.py

3. Create src/integrations/google/oauth.py:
   - GoogleOAuthService class:
     - get_authorization_url(state, scopes)
     - handle_callback(code, state)
     - exchange_code_for_token(code)
     - refresh_access_token(refresh_token)
     - validate_scopes(token, required_scopes)

4. Define Google scopes in src/integrations/google/scopes.py:
   - CALENDAR_READONLY
   - CALENDAR_EVENTS
   - GMAIL_READONLY
   - GMAIL_SEND
   - Group scopes by feature; least-privilege per feature flag (TRD §3.1)

5. Create src/api/routes/oauth.py:
   - GET /oauth/google/authorize
   - GET /oauth/google/callback
   - GET /oauth/google/status
   - POST /oauth/google/revoke

6. Add to settings:
   - google_client_id (required)
   - google_client_secret (required)
   - google_redirect_uri
   - Add validation for production

7. Create setup documentation:
   - Google Cloud Console setup
   - OAuth consent screen config
   - Required APIs to enable

Test the full OAuth flow locally.
```

### Step 22: Calendar Read Integration via MCP

```text
Integrate Google Calendar reads through an MCP server instead of a
hand-built API client (PRD §7 hybrid architecture).

Building on Steps 1-21:

1. Write tests in tests/test_calendar_mcp.py:
   - Test MCP client connection lifecycle (connect, list tools, disconnect)
   - Test typed wrappers over list-events / get-event / free-busy tools
   - Test error mapping (MCP tool errors -> ExternalServiceError)
   - Mock the MCP server; no live Google calls in CI

2. Add the MCP Python SDK via uv

3. Create src/integrations/mcp/__init__.py and src/integrations/mcp/client.py:
   - McpToolClient: thin async wrapper around an MCP server connection
     - call_tool(name, arguments) with timeout and retry/backoff
     - tool discovery + JSONSchema validation of arguments
   - Server command/URL configured per integration in settings

4. Create src/integrations/calendar_read.py:
   - CalendarReadService — used by BOTH deterministic services and the
     agent (Step 26), so reads have one tested code path:
     - list_events(calendar_id, time_min, time_max)
     - get_event(calendar_id, event_id)
     - get_freebusy(emails, time_min, time_max)
   - Returns typed Pydantic models in src/schemas/calendar.py:
     Calendar, Event, Attendee, FreeBusySlot, TimeSlot
   - Normalize timezones and expand recurring-event instances at this
     boundary so downstream code never touches raw API payloads

5. Wire OAuth: pass stored credentials (Step 19 TokenManager) into the MCP
   server's config/environment; refresh and retry on auth errors

6. Add read endpoints:
   - GET /calendars/{id}/events
   - POST /calendars/freebusy

Ensure NO calendar write tool is exposed through this path — writes belong
exclusively to the Scheduler service (Step 24).
```

### Step 23: Availability Service

```text
Build deterministic availability computation on top of MCP calendar reads.
This is pure Python — no LLM involvement — because slot math must be exact,
testable, and fast (TRD §12 latency targets).

Building on Steps 1-22:

1. Write tests in tests/test_availability.py:
   - Test busy-slot merge across multiple calendars
   - Test working-hours overlay per person/timezone
   - Test buffer application (before/after, from Policy)
   - Test slot splitting by duration and grid alignment
   - Test DST-transition and cross-timezone edge cases

2. Create src/services/availability_service.py:
   - AvailabilityService class:
     - get_busy_slots(user_id, start, end)
     - find_free_slots(attendees, duration, range)
     - check_slot_availability(user_id, slot)
     - get_working_hours(person, date)  # tz-aware, from Policy
     - apply_buffer_time(slots, before, after)

3. Create src/utils/time_utils.py:
   - merge_overlapping_slots(slots)
   - subtract_slots(available, busy)
   - split_slot_by_duration(slot, duration)
   - align_to_time_grid(slot, grid_minutes)

4. Create src/schemas/availability.py:
   - AvailabilityRequest / AvailabilityResponse
   - BusySlot / FreeSlot

5. Add availability endpoints:
   - POST /availability/check
   - POST /availability/find-slots
   - GET /availability/working-hours

Policies (Step 17) drive buffers, working hours, and no-meeting days.
Ensure accurate availability calculation under DST and TZ spread.
```

### Step 24: Scheduler Write Service (Two-Phase Commit)

```text
Implement the deterministic calendar write path with two-phase commit
(TRD §2.3). This service is the ONLY component allowed to write to Google
Calendar — the agent (Step 26) gets no calendar-write tool.

Building on Steps 1-23:

1. Write tests in tests/test_scheduler_writes.py:
   - Test dry-run validation failures: overlap, recurrence break,
     outside working hours, DST/holiday hits
   - Test idempotency (same key submitted twice -> exactly one write)
   - Test post-commit re-validation and automatic rollback
   - Test soft-hold creation, TTL expiry, and cleanup
   - Test pre-state snapshot capture for undo

2. Add google-api-python-client via uv (write operations only)

3. Create src/integrations/google/calendar_writer.py:
   - CalendarWriter class:
     - create_event(calendar_id, event, idempotency_key)
     - update_event(calendar_id, event_id, changes, idempotency_key)
     - delete_event(calendar_id, event_id, idempotency_key)
   - Retry with exponential backoff; rate-limit aware

4. Create src/services/scheduler_service.py:
   - SchedulerService class:
     - dry_run(intent) -> ValidationReport (fresh free/busy via Step 22,
       recurrence integrity, buffers, TZ/DST/holiday checks)
     - commit(intent, idempotency_key) -> CommitResult
     - post_validate(commit_result)  # re-check; roll back on failure
     - create_hold(slot, ttl) / expire_holds()  # soft holds, PRD R4
     - snapshot_pre_state(event)  # retained N days for undo (TRD §7)

5. Record every write to the audit log (full Decision Logger in Step 34)

6. Add internal endpoints (JWT-protected):
   - POST /scheduler/dry-run
   - POST /scheduler/commit
   - POST /scheduler/holds
   - DELETE /scheduler/holds/{id}

Ensure no write reaches Google Calendar without a passing dry run.
```

### Step 25: Conflict Detection

```text
Build conflict detection on top of the availability service, promoting
conflicts to ScheduleIntents for the orchestrator.

Building on Steps 1-24:

1. Write comprehensive tests in tests/test_conflict_detection.py:
   - Test overlapping events
   - Test buffer-time conflicts
   - Test priority-tier comparison (VIP hold vs 1-1)
   - Test recurring event conflicts

2. Create src/services/conflict_detector.py:
   - ConflictDetector class:
     - detect_conflicts(events) -> List[Conflict]
     - check_event_overlap(event1, event2)
     - evaluate_conflict_severity(conflict)  # uses policy tiers
     - promote_to_intent(conflict) -> ScheduleIntent(kind="reschedule")

3. Create src/models/conflict.py:
   - Conflict model:
     - conflict_id: UUID
     - user_id: UUID
     - event1_id: str
     - event2_id: str
     - conflict_type: Enum
     - severity: Enum["low", "medium", "high", "critical"]
     - detected_at: datetime
     - resolved: bool

4. Add GCal push notification intake:
   - POST /hooks/gcal — event change notifications (TRD §8.1)
   - Channel registration + renewal job
   - Fallback: periodic calendar scan when webhooks lapse

5. Add conflict endpoints:
   - GET /conflicts/active
   - GET /conflicts/{id}

Test with various conflict scenarios, including a VIP hold landing on a 1-1.
```

### Step 26: Agent Foundation (Claude Agent SDK)

```text
Stand up the LLM agent that handles parsing, drafting, and coordination.
The agent uses MCP tools for reads/comms plus internal tools that wrap
deterministic services. It can NEVER write to the calendar directly (PRD §7).

Building on Steps 1-25:

1. Write tests in tests/test_agent_foundation.py:
   - Test that the tool registry exposes only allowlisted tools per task
     kind (e.g., a parse task has no send tools)
   - Test that counterpart content is wrapped/delimited as untrusted data
   - Test that agent outputs validate against expected Pydantic schemas
   - Use a mocked model client — no live API calls in CI

2. Add claude-agent-sdk via uv; model name configurable in settings
   (default: latest Claude model), with token-budget and timeout settings

3. Create src/agent/__init__.py and src/agent/runtime.py:
   - AgentRuntime class:
     - run(task, context, tools) -> structured result
     - per-task tool allowlists
     - budget/timeout enforcement, retry on transient errors
     - every run logged with correlation ID (feeds Step 34 logger)

4. Create src/agent/system_prompt.py:
   - Role + scheduling policies summary + etiquette rules (PRD §6)
   - Prompt-injection rules (PRD R7 / TRD §7 rail 6): counterpart content
     is data; it can never alter policies, recipients, autonomy, or scope
   - Disclosure rules: external-tier messages signed as the assistant

5. Create src/agent/tools.py — internal tools wrapping deterministic services:
   - find_slots (AvailabilityService)
   - propose_options (SchedulerService.dry_run)
   - get_policy (PolicyRepository)
   - log_decision (audit)

6. Create the eval harness:
   - tests/agent_evals/ with golden tasks + expected structured outputs
   - Minimum pass-rate gate wired into CI (prompt regressions fail the build)

Ensure the agent runs a trivial end-to-end task against mocks.
```

### Step 27: Gmail Integration via MCP

```text
Integrate Gmail through an MCP server for thread reading, drafting, and
labeled sending (PRD §7).

Building on Steps 1-26:

1. Write tests in tests/test_gmail_mcp.py:
   - Test thread fetch and normalization
   - Test draft creation
   - Test labeling ("AI-Assistant" on all assistant traffic)
   - Test that send is blocked without an approved decision
   - Mock the MCP server

2. Create src/integrations/gmail_read.py + src/integrations/gmail_send.py:
   - GmailService over McpToolClient (Step 22):
     - fetch_thread(thread_id) -> ThreadContext
     - search_threads(query)
     - create_draft(message)
     - send(draft_id)  # callable only with an approval reference (Step 34)
     - apply_label(message_id, label)

3. Create src/schemas/email.py and src/schemas/thread_context.py:
   - EmailMessage, EmailThread, EmailDraft, EmailAddress
   - ThreadContext: subject, participants, latest_message, message_count
   - Smart truncation: keep recent context, strip quoted text/signatures,
     preserve key information (token-bounded for agent input)

4. Add Gmail intake webhook:
   - POST /hooks/gmail — inbound message envelope (TRD §8.1)

5. Gmail-specific settings:
   - gmail_label_prefix: "AI-Assistant"
   - gmail_watch_labels: ["INBOX"]

6. Add endpoints:
   - GET /emails/threads/{id}
   - POST /emails/search

Thread content returned to the agent must pass through the untrusted-data
wrapper from Step 26.
```

### Step 28: Meeting Request Extraction (Structured Output)

```text
Extract ScheduleIntents from emails and Slack messages using agent
structured output. This replaces the regex/dateutil NLP parser from the
original plan — enums + Pydantic schemas instead of regex (CLAUDE.md).

Building on Steps 1-27:

1. Build a golden fixture set FIRST in tests/fixtures/meeting_requests/:
   - ~30 real-shaped emails/DMs: explicit times, relative times
     ("early next week"), TZ hints, multiple attendees, vague asks,
     non-requests (newsletters), and adversarial content (injection attempts)

2. Write tests in tests/test_meeting_extraction.py:
   - Test extraction accuracy against the golden set (set explicit
     precision targets; failures block CI)
   - Test that ambiguous inputs yield LOW confidence, never guesses
   - Test that injection attempts extract nothing actionable beyond the
     scheduling ask

3. Create src/schemas/meeting_request.py:
   - MeetingRequest model:
     - requested_times: List[TimeSlot]
     - duration_minutes: int
     - attendees: List[str]
     - purpose: str
     - urgency: Enum["low", "normal", "high"]
     - kind: Enum["new", "reschedule", "cancel"]
     - confidence: float

4. Create src/agent/extractors.py:
   - parse_email(thread_context) -> MeetingRequest
   - parse_slack(message_context) -> MeetingRequest
   - Structured output against the Pydantic schema via AgentRuntime
   - Below-threshold confidence routes to approval — never auto-propose
     from a guess (PRD story B3)

5. Promote high-confidence extractions to ScheduleIntent records

6. Add endpoint:
   - POST /meetings/parse-request

Track extraction accuracy over time; the golden set grows with every
real-world miss.
```

### Step 29: Slack App and Event Handler

```text
Set up the Slack app and event handling for DMs, threads, and slash commands.
Inbound events arrive via webhooks (FastAPI); outbound messages go through
the Slack SDK/MCP tools.

Building on Steps 1-28:

1. Write tests in tests/test_slack.py:
   - Test event signature verification
   - Test event routing (message.im, app_mention, reaction_added)
   - Test slash command parsing (/findtime 30m this week @Alex)
   - Test DM send and thread reply (mocked)
   - Test rate limiting/backoff

2. Create src/integrations/slack/__init__.py and client.py:
   - SlackService:
     - verify_signature(request)
     - send_dm(user_id, text, blocks)
     - reply_to_thread(channel, thread_ts, text)
     - get_user_info(user_id)
   - Rate limiting with backoff and queueing

3. Create src/integrations/slack/events.py:
   - SlackEventHandler:
     - handle_event(event_data) — routes by type
     - handle_message(event) / handle_app_mention(event)
     - handle_reaction(event)  # 👍/👎 capture feeds §5 satisfaction metric
     - handle_slash_command(command)

4. Create src/api/routes/slack.py:
   - POST /slack/events — event webhook (URL verification included)
   - POST /slack/slash — slash commands
   - POST /slack/interactive — button/select actions (used in Step 30)

5. Create Slack app manifest (slack-app-manifest.yml):
   - Scopes per TRD §3.2; event subscriptions; slash commands;
     interactive components

6. Setup documentation: app creation, OAuth, event URL configuration

Slack message content passed to the agent goes through the untrusted-data
wrapper from Step 26.
```

### Step 30: Approval Cards and Slack Interactivity

```text
Build the approval surface: Slack DM cards with Approve / Reject / Edit
(PRD R6 — this is the most-used UX in the approval-first MVP).

Building on Steps 1-29:

1. Write tests in tests/test_approval_cards.py:
   - Test card rendering for each intent kind (reschedule, new, cancel)
   - Test Approve/Reject/Edit action payload handling
   - Test that cards show the decision rationale and top feature
     attributions (TRD §6 explainability)
   - Test daily brief assembly

2. Create src/services/approval_cards.py:
   - Block Kit builders:
     - build_approval_card(decision) — what/why/who, two options,
       Approve / Reject / Edit buttons
     - build_daily_brief(date) — top conflicts, pending approvals,
       holds expiring (PRD R8, story A2)
     - build_action_summary(result) — post-action visibility DM (story A1)

3. Wire /slack/interactive:
   - Route button actions to the approval service (Step 34 completes this;
     stub the state transition for now)
   - Edit opens a modal for inline draft edits before approval

4. Schedule the 9:00 AM daily brief job (user-local timezone)

5. P95 < 1.0s round-trip for interactive actions (TRD §12) — keep
   handlers thin, defer work to the queue

The web console remains audit/history-only for MVP (PRD R6); do not build
approval UI outside Slack.
```

### Step 31: Message Templates and Drafting

```text
Build the template library and agent drafting flow with tone-by-tier and
the external disclosure rule.

Building on Steps 1-30:

1. Write tests in tests/test_drafting.py:
   - Test template rendering with variable substitution
   - Test tone selection by policy tier (exec-concise, friendly-internal,
     customer-professional)
   - Test that EXTERNAL drafts (Customer/Hiring-external tiers) always
     carry the assistant signature, and internal drafts never do (PRD R7)
   - Test one-ask-per-message and option bullet formatting (PRD §6)

2. Add jinja2 via uv; create templates/:
   - email/reschedule_request.{html,txt}
   - email/external_meeting_request.{html,txt}  # signed "Cal — Samiur's
     scheduling assistant" (PRD §13)
   - slack/find_time_dm.json
   - base/email_base.html

3. Create src/services/template_engine.py:
   - render_template(name, context); custom filters:
     format_datetime(dt, tz), format_duration, format_attendee_list,
     escape_slack_text

4. Create src/agent/drafting.py:
   - draft_message(intent, context, channel) -> Draft
   - Templates are the skeleton; the agent personalizes within them
     (AgentRuntime, Step 26) — it cannot remove the disclosure signature
     or add recipients
   - Tone preferences read from memory once Step 32 lands

5. Add draft endpoints:
   - POST /drafts (generate)  - PUT /drafts/{id} (edit)
   - Sending remains gated on approval (Steps 27, 34)

Test drafts across tiers and channels against PRD §13 examples.
```

### Step 32: Zep Memory Integration

```text
Integrate Zep memory graphs for durable preferences (MVP scope per PRD
changelog 2026-06-10; ontology and flows in TRD §5).

Building on Steps 1-31:

1. Write tests in tests/test_memory.py:
   - Test entity/edge upserts (Person, MeetingSeries, Preference, Travel)
   - Test read paths return token-bounded context
   - Test write-backs after accepted/declined options
   - Test validity windows (expired preferences excluded)
   - Test redaction: no raw email/Slack content stored, evidence as
     hashed references
   - Mock the Zep client

2. Add the Zep client via uv; settings for API key/URL

3. Create src/memory/ontology.py:
   - Entities: Person, Team, MeetingSeries, Preference(TimeWindow,
     Channel, Tone), Policy, Travel, Holiday
   - Edges: reports_to, has_series, prefers_slot, communicates_on,
     tone_pref, timezone_of, on_pto_on, blackout (TRD §5.1)

4. Create src/memory/reader.py:
   - fast_context(thread)  # basic mode + last 4-6 messages, for Slack
   - precise_context(series_id, counterpart)  # graph query filtered to
     MeetingSeries/Preference/Travel/Holiday, token-bounded custom block
     (TRD §5.2)

5. Create src/memory/writer.py:
   - upsert_preference(kind, value, evidence_ref, valid_from, valid_to)
   - record_outcome(intent, accepted_slot)  # e.g., learned "Tue/Thu AM"
   - insert_travel(window)  # transient, auto-expires

6. Wire into the agent: context blocks feed AgentRuntime runs (Step 26);
   write-backs fire after successful bookings (orchestrator, Step 35)

7. Add endpoints:
   - POST /memory/upsert
   - GET /memory/context?mode=basic|custom&series_id=...

Privacy: structured facts only; memory snapshot hashes recorded in the
decision log (Step 34).
```

### Step 33: Scheduler Slot Finder

```text
Implement the slot-finding and ranking algorithm for meeting proposals.

Building on Steps 1-32:

1. Write comprehensive tests in tests/test_slot_finder.py:
   - Test common-availability intersection across attendees
   - Test constraint satisfaction (window, duration, working hours)
   - Test preference weighting from memory (e.g., afternoon bias)
   - Test cadence preservation for series (same weekday/time-of-day bias,
     TRD §2.3 cadence keeper)

2. Create src/algorithms/slot_finder.py:
   - SlotFindingAlgorithm:
     - find_common_availability(attendees, range)  # via AvailabilityService
     - apply_constraints(slots, policy)
     - score_slot_quality(slot, preferences)  # memory-weighted
     - detect_back_to_back(slots)

3. Create src/services/slot_proposer.py:
   - propose_slots(intent) -> List[TimeSlot]  # ranked, >= 2 options (PRD R4)
   - Optimization strategies: minimize TZ pain, preserve focus blocks,
     maintain series cadence, balance calendar density
   - Each proposal passes SchedulerService.dry_run before being offered

4. Create src/models/constraints.py:
   - TimeConstraint, DurationConstraint, AttendeeConstraint

5. Add scheduler endpoints:
   - POST /scheduler/find-slots
   - POST /scheduler/evaluate-slot

Latency target: initial options within 60s of trigger (PRD §10).
Test with complex scenarios: 3+ attendees, cross-TZ, dense calendars.
```

### Step 34: Approval Workflow, Decision Logger, and Shadow Scorer

```text
Build the approval lifecycle, the decision audit log, and the
shadow-mode confidence scorer.

IMPORTANT (PRD R6): approval mode has NO timeout auto-proceed. An expired
approval becomes status "expired" and surfaces in the daily brief — it
never executes on its own.

Building on Steps 1-33:

1. Write tests in tests/test_approval_workflow.py:
   - Test approval creation and state transitions
     (pending -> approved | rejected | expired)
   - Test that expired approvals NEVER execute and appear in the brief
   - Test that send/commit paths require an approved decision reference
   - Test rejection triggers alternative proposals (PRD §8.1 reject flow)

2. Create src/models/approval.py:
   - Approval model:
     - approval_id, decision_id: UUID
     - status: Enum["pending", "approved", "rejected", "expired"]
     - created_at, expires_at: datetime
     - approved_by: Optional[UUID]
     - approval_method: Enum["slack_card", "console"]  # no timeout_default

3. Create src/services/decision_logger.py (PRD §5 data source):
   - Structured events with correlation IDs (TRD §10):
     decision_taken, message_sent, event_moved, approval_resolved,
     extraction_scored
   - Each decision records: inputs, policy snapshot hash, memory snapshot
     hash, model outputs, human action, effects (TRD §2.6)
   - Redact PII in log payloads

4. Create src/services/confidence_scorer.py (SHADOW for all of MVP):
   - Features per TRD §6.1: policy tier, attendee count, is-series,
     TZ/DST spread, counterpart acceptance history, memory strength,
     message ambiguity
   - score(decision) -> ShadowVerdict{confidence, would_auto_send, top_5_attributions}
   - Verdict is LOGGED on every decision and shown on the approval card;
     it never gates execution in MVP. Auto-send thresholds (TRD §6.2)
     activate in rollout Phase 2 after calibration.

5. Create src/services/approval_service.py:
   - create_approval(decision, expires_at)
   - process_action(approval_id, action, actor)
   - expire_stale() job -> mark expired + queue for daily brief
   - get_pending(user_id)

6. Complete the /slack/interactive wiring from Step 30; add endpoints:
   - GET /approvals/pending
   - POST /approvals/{id}/approve | /reject

Test the full lifecycle including expiry and rejection-with-alternatives.
```

### Step 35: Orchestrator with State Machine and Shadow Mode

```text
Build the core orchestrator that coordinates all components, including
the shadow mode required for rollout Phase 0 (PRD §12).

Building on Steps 1-34:

1. Write tests in tests/test_orchestrator.py:
   - Test state transitions and persistence
   - Test full workflows end-to-end against mocks
   - Test SHADOW_MODE: drafts produced, verdicts logged, but zero sends
     and zero calendar writes
   - Test failure recovery and compensation (rollback)
   - Test follow-up/escalation flow (PRD stories B2/B3): one follow-up
     per channel, channel escalation, max two proposal rounds, then brief

2. Create src/models/workflow_state.py:
   - WorkflowState enum: INTENT_CREATED, ANALYZING, AWAITING_APPROVAL,
     APPROVED, EXECUTING, COMPLETED, FAILED, SHADOW_LOGGED

3. Create src/services/orchestrator.py:
   - Orchestrator class:
     - process_intent(intent) -> Decision
       (context: policy + memory context block + thread tail, TRD §2.1)
     - execute_decision(decision)  # gated on approval; respects SHADOW_MODE
     - handle_failure(error, state)  # compensation actions

4. Create src/services/workflow_engine.py:
   - State machine with transition rules, persistence, retries

5. Implement core workflows:
   - Reschedule 1-1 (conflict -> propose -> approve -> commit -> notify
     -> memory write-back; TRD §17.1)
   - New meeting request (parse -> propose -> approve -> commit)
   - Follow-up/escalation (B2) and proposal-round limits (B3)
   - Hold management (create, expire, clean)

6. Wire intake to intents: POST /intents (TRD §8.1); conflict detector,
   email webhook, and Slack events all promote into this single path

7. Add endpoints:
   - POST /workflows/start
   - GET /workflows/{id}/status
   - POST /workflows/{id}/retry

8. Shadow-mode reporting:
   - Aggregate shadow logs into the KPI baseline report (automation rate,
     would-have-sent accuracy, time-to-propose) to confirm or revise
     PRD §1 targets at the end of Phase 0

Test end-to-end: a VIP hold conflicting with a 1-1 produces two proposed
options, an approval card, a committed move on approval, a counterpart
notification, a memory write-back, and a complete audit trail — and in
shadow mode produces everything except the send and the write.
```

---

## Testing Strategy

Each step includes:
1. **Unit tests** - Test individual components
2. **Integration tests** - Test component interactions (mocked MCP servers and model client; no live external calls in CI)
3. **Agent evals** - Golden-task pass-rate gates from Step 26 onward
4. **E2E tests** - Test full user scenarios (from Step 25+)

## Deployment Strategy

1. Local development with Docker Compose
2. CI/CD with GitHub Actions (Steps 4-8)
3. Staging environment on Vercel/Railway
4. Production deployment with monitoring

## Next Steps After MVP

1. Auto-send enablement for 1-1s (rollout Phase 2, thresholds calibrated from shadow logs)
2. Travel mode + nightly sanity sweeps (TRD §7)
3. Candidate interview templates and customer call presets (ATS/CRM, feature-flagged)
4. Learning loop v2: mining historical accept/decline patterns (PRD post-MVP)
5. Performance optimization
6. Production hardening

## Success Criteria

- All tests passing (unit, integration, agent evals, E2E)
- Core workflows functioning end-to-end
- Approval workflow operational (strictly approval-first; no auto-proceed)
- Calendar writes only via the Scheduler service with two-phase commit
- Email/Slack communication functional via MCP, with external disclosure
- Policy engine evaluating correctly
- Shadow-mode baseline captured and KPI targets confirmed or revised

## Risk Mitigation

- Each step is independently testable
- No step breaks previous functionality
- Gradual complexity increase
- Feature flags for risky features (including SHADOW_MODE)
- Comprehensive error handling at each layer
- Untrusted-input wrapping for all counterpart content reaching the agent
