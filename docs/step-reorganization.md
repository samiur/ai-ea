# Step Reorganization: CI/CD Early Integration

## Rationale

Moving CI/CD infrastructure to steps 4-8 (immediately after basic project setup) provides:

1. **Immediate Quality Feedback** - Catch issues on every commit from day one
2. **Better TDD Support** - Automated test running supports test-driven development
3. **Prevents Technical Debt** - Quality gates prevent accumulation of issues
4. **Team Collaboration** - Consistent standards from the start

## New Step Ordering

### Phase 1: Foundation & CI/CD (Steps 1-10)

- **Step 1**: Project Initialization *(unchanged)*
- **Step 2**: Basic FastAPI Application *(unchanged)*
- **Step 3**: Settings and Configuration *(unchanged)*
- **Step 4**: Basic GitHub Actions Workflow *(moved from Step 31)*
- **Step 5**: Test Execution in CI *(moved from Step 32)*
- **Step 6**: Code Quality Checks *(moved from Step 33)*
- **Step 7**: Docker Build and Registry *(moved from Step 34)*
- **Step 8**: Deployment Automation *(moved from Step 35)*
- **Step 9**: Docker Compose for PostgreSQL *(was Step 4)*
- **Step 10**: API Error Handling and Responses *(was Step 10)*

### Phase 2: Database & Models (Steps 11-17)

- **Step 11**: SQLModel Setup and Connection *(was Step 5)*
- **Step 12**: Person and Policy Data Models *(was Step 6)*
- **Step 13**: Meeting Series and Related Models *(was Step 7)*
- **Step 14**: Database Migrations with Alembic *(was Step 8)*
- **Step 15**: Repository Pattern Implementation *(was Step 9)*
- **Step 16**: Feature Flags System *(was Step 11)*
- **Step 17**: Policy YAML Loader and Parser *(was Step 12)*

### Phase 3: Authentication & Security (Steps 18-20)

- **Step 18**: OAuth Configuration Models *(was Step 13)*
- **Step 19**: Secure Token Storage *(was Step 14)*
- **Step 20**: JWT Middleware for Internal APIs *(was Step 15)*

### Phase 4: Calendar Core (Steps 21-25)

> Steps 21-35 were rewritten on 2026-06-10 for the hybrid agent+MCP architecture (PRD §7), so the "was Step N" mapping ends here.

- **Step 21**: Google OAuth Credential Setup
- **Step 22**: Calendar Read Integration via MCP
- **Step 23**: Availability Service
- **Step 24**: Scheduler Write Service (Two-Phase Commit)
- **Step 25**: Conflict Detection

### Phase 5: Agent & Communication (Steps 26-32)

- **Step 26**: Agent Foundation (Claude Agent SDK)
- **Step 27**: Gmail Integration via MCP
- **Step 28**: Meeting Request Extraction (Structured Output)
- **Step 29**: Slack App and Event Handler
- **Step 30**: Approval Cards and Slack Interactivity
- **Step 31**: Message Templates and Drafting
- **Step 32**: Zep Memory Integration

### Phase 6: Orchestration (Steps 33-35)

- **Step 33**: Scheduler Slot Finder
- **Step 34**: Approval Workflow, Decision Logger, and Shadow Scorer
- **Step 35**: Orchestrator with State Machine and Shadow Mode

## Implementation Impact

### Benefits of Early CI/CD

1. **Step 4-8 Foundation**:
   - All subsequent code automatically tested
   - Code quality enforced from first database model
   - Docker builds validate deployment early

2. **Parallel Development**:
   - Team can work on features knowing CI catches issues
   - PR reviews focus on logic, not style/quality
   - Automated testing reduces manual QA burden

3. **Faster Feedback**:
   - Developers know within minutes if code breaks
   - Type errors caught before manual testing
   - Security vulnerabilities detected early

### Migration Path

For existing work on Step 1 (already completed):

1. Next PR should implement Steps 2-3 (FastAPI + Settings)
2. Then immediately implement Steps 4-8 (CI/CD)
3. Continue with Step 9+ (Database, Models, etc.)

This ensures CI/CD is in place before significant code volume accumulates.

## Timeline Adjustment

**Original Plan**: CI/CD at end (Steps 31-35)
**New Plan**: CI/CD early (Steps 4-8)

**Development Flow**:
```
Week 1: Steps 1-3   (Project setup + FastAPI)
Week 2: Steps 4-8   (Complete CI/CD pipeline)
Week 3: Steps 9-15  (Database + Models)
Week 4: Steps 16-20 (Auth + Security)
...
```

This front-loads infrastructure work but pays dividends throughout development.
