# CLAUDE.md - AI Executive Assistant Project

## About This Project

This is Samiur's AI Executive Assistant for calendar management and coordination. The assistant automatically handles scheduling, rescheduling, and meeting coordination across Google Calendar, Gmail, and Slack with policy-driven decision making and approval workflows.

## My Name

For this project, call me **Cal** (short for Calendar Assistant).

## Development Approach

### Test-Driven Development (TDD)

This project strictly follows TDD principles:
1. **Write tests first** - Always write failing tests before implementation
2. **Implement minimally** - Only write enough code to make tests pass
3. **Refactor continuously** - Clean up while keeping tests green

### CI/CD First

**IMPORTANT**: We implement CI/CD infrastructure **early** (Steps 4-8) to ensure:
- Automated testing on every commit
- Code quality gates from day one
- Immediate feedback on issues
- No technical debt accumulation

All code after Step 3 runs through:
- Automated pytest execution with coverage
- Ruff linting and formatting checks
- Mypy strict type checking
- Security scanning (Bandit, pip-audit)
- Docker build validation

### Implementation Strategy

We follow a **step-by-step incremental approach** with 35 carefully ordered steps:

**Phase 1: Foundation & CI/CD (Steps 1-10)**
- Steps 1-3: Basic project setup, FastAPI, settings
- **Steps 4-8: Complete CI/CD pipeline** ← We prioritize this!
- Steps 9-10: Database setup, error handling

**Phase 2-6**: Database, auth, integrations, communication, orchestration

See `plan.md` for detailed step-by-step prompts and `todo.md` for current progress.

## Code Standards

### Python Conventions

- **Type annotations**: Use modern syntax (`str | None` instead of `Optional[str]`)
- **Pydantic**: Always use `Annotated[Type, Field(...)]` pattern
- **Enums over regex**: For finite sets of values (better for LLM structured output)
- **Async-first**: All I/O operations should be async
- **Comments**: Every file starts with 2-line `ABOUTME:` comment

### Quality Requirements

- **All tests must pass** - No exceptions
- **Type checking**: `mypy src/ --strict` must pass
- **Linting**: `ruff check .` must pass with no errors
- **Formatting**: `ruff format .` applied to all code
- **Coverage**: Aim for >80% test coverage

### Tools & Dependencies

- **Package management**: uv (exclusively - no pip/poetry)
- **Web framework**: FastAPI
- **Database**: PostgreSQL + SQLModel ORM + Alembic migrations
- **Testing**: pytest + pytest-asyncio
- **Type checking**: mypy with pydantic plugin
- **Linting/formatting**: ruff
- **Security**: bandit for security linting

## Current Status

**Completed**:
- ✅ Step 1: Project initialization with uv and pyproject.toml

**Next Steps**:
1. Step 2: Basic FastAPI application
2. Step 3: Settings and configuration
3. **Steps 4-8: CI/CD infrastructure** (priority!)

See `todo.md` for detailed progress tracking.

## Key Documents

- **`PRD.md`**: Product requirements and user stories
- **`TRD.md`**: Technical design and architecture
- **`plan.md`**: 35-step implementation plan with detailed prompts
- **`todo.md`**: Current progress and task tracking
- **`docs/cicd-overview.md`**: CI/CD infrastructure details
- **`docs/step-reorganization.md`**: Why we moved CI/CD early

## Decision Log

### Why CI/CD Early? (Steps 4-8)

**Original plan**: CI/CD at end (Steps 31-35)
**Updated plan**: CI/CD immediately after basic setup (Steps 4-8)

**Rationale**:
- Get immediate quality feedback on every commit
- Catch type errors, linting issues, test failures immediately
- Support TDD with automated test execution
- Prevent technical debt before significant code volume accumulates
- Enable confident collaboration when team scales

This was a deliberate architectural decision to prioritize development velocity and code quality from the start.

## Working with Me (Cal)

- I follow the implementation plan in `plan.md` step-by-step
- I always write tests first (TDD)
- I ask for clarification rather than making assumptions
- I update documentation as we progress
- I'm pedantic about code quality because CI/CD catches everything
- I reference code locations with `file:line` format

## Project Philosophy

**Build for production from day one**:
- Every feature is tested
- Every commit goes through CI
- Every deployment is automated
- Every decision is logged

**Incremental progress**:
- Small steps that build on each other
- No big jumps in complexity
- Each step independently testable
- No orphaned or hanging code

**Quality over speed**:
- Strict type checking from the start
- Automated quality gates
- Security scanning on every build
- Clean, maintainable code

---

**Last updated**: 2025-10-10 (after CI/CD reorganization)
