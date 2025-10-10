# CI/CD Overview for AI Executive Assistant

## Introduction

This document outlines the CI/CD (Continuous Integration/Continuous Deployment) infrastructure for the AI Executive Assistant project. The CI/CD pipeline is implemented using GitHub Actions and follows industry best practices for automated testing, code quality checks, and deployment automation.

> **Important**: CI/CD infrastructure is implemented **early in the project** (Steps 4-8) to provide immediate quality feedback and support test-driven development from the start. This ensures all subsequent code is automatically tested and validated.

## Architecture

### Pipeline Stages

The CI/CD pipeline consists of five main stages, implemented across **Steps 4-8** (moved early in the plan):

1. **Basic Workflow Setup** (Step 4)
2. **Test Automation** (Step 5)
3. **Code Quality Checks** (Step 6)
4. **Docker Build & Registry** (Step 7)
5. **Deployment Automation** (Step 8)

## Stage Details

### Stage 1: Basic GitHub Actions Workflow (Step 4)

**Purpose**: Establish the foundation for CI/CD automation

**Components**:
- GitHub Actions workflow configuration
- Python 3.12 setup with uv
- Dependency caching
- Multi-version testing matrix
- Status badges

**Triggers**:
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop`
- Manual workflow dispatch

**Key Files**:
- `.github/workflows/ci.yml`

### Stage 2: Test Execution in CI (Step 5)

**Purpose**: Ensure all tests run automatically on every commit

**Components**:
- PostgreSQL service container for integration tests
- Pytest execution with coverage reporting
- JUnit XML test reporting
- Test result annotations on PRs
- Coverage tracking

**Testing Layers**:
- Unit tests
- Integration tests
- End-to-end tests

**Outputs**:
- Test reports (JUnit XML)
- Coverage reports (XML format)
- PR annotations with test results

### Stage 3: Code Quality Checks (Step 6)

**Purpose**: Maintain high code quality standards

**Components**:
- **Linting**: Ruff for code style and formatting
- **Type Checking**: Mypy with strict mode
- **Security Scanning**: Bandit for security vulnerabilities
- **Dependency Audit**: pip-audit for vulnerable dependencies

**Quality Gates**:
- All linting checks must pass
- Type checking must pass with strict mode
- No high/critical security vulnerabilities
- Formatting must match standards

**Caching**:
- uv package cache
- Mypy cache
- Ruff cache

### Stage 4: Docker Build and Registry (Step 7)

**Purpose**: Build and publish containerized application

**Components**:
- Multi-stage Docker build using uv
- GitHub Container Registry (ghcr.io)
- Docker layer caching
- Image vulnerability scanning with Trivy
- Multi-platform builds (amd64, arm64)

**Tagging Strategy**:
- `latest` - main branch builds
- `develop` - develop branch builds
- `pr-{number}` - pull request builds
- `sha-{commit}` - commit-specific tags
- `v{version}` - semantic version tags

**Security**:
- Trivy vulnerability scanning
- Scan results uploaded to GitHub Security
- Only scan-passed images are pushed

### Stage 5: Deployment Automation (Step 8)

**Purpose**: Automate deployments to staging and production

**Components**:

#### Environments
- **Staging**: Auto-deploy from `develop` branch
- **Production**: Manual approval required, deploy from `main` tags

#### Deployment Process
1. Pull Docker image from registry
2. Run database migrations
3. Deploy application
4. Run health checks
5. Execute smoke tests
6. Send notifications

#### Rollback Strategy
- Automatic rollback on health check failure
- Manual rollback scripts available
- Database migration rollback support

#### Monitoring
- Deployment frequency tracking
- Success/failure rate monitoring
- Deployment duration metrics
- Automated alerts on failures

## Workflow Files

### Primary Workflows

1. **`.github/workflows/ci.yml`**
   - Main CI pipeline
   - Runs on all pushes and PRs
   - Jobs: test, lint, type-check, build

2. **`.github/workflows/deploy-staging.yml`**
   - Staging deployment
   - Auto-deploys from develop branch
   - No approval required

3. **`.github/workflows/deploy-production.yml`**
   - Production deployment
   - Requires manual approval
   - Deploys from tagged releases only

## Required Secrets

### GitHub Repository Secrets

**For CI/CD**:
- `GHCR_TOKEN` - GitHub Container Registry authentication

**For Integration Tests**:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `SLACK_BOT_TOKEN` - Slack bot token for testing

**For Deployments**:
- Environment-specific secrets configured in GitHub Environments

### GitHub Environment Secrets

**Staging Environment**:
- `DATABASE_URL` - Staging database connection
- `REDIS_URL` - Staging Redis connection
- `SECRET_KEY` - Application secret key
- `GOOGLE_CLIENT_ID` - Google OAuth credentials
- `GOOGLE_CLIENT_SECRET`
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`

**Production Environment**:
- Same as staging, but with production values
- Additional security credentials as needed

## Branch Protection Rules

### Main Branch
- Require pull request reviews (1 reviewer minimum)
- Require status checks to pass:
  - `test`
  - `lint`
  - `type-check`
  - `build`
- Require branches to be up to date
- Require conversation resolution before merging
- Require signed commits (optional)

### Develop Branch
- Require status checks to pass
- Allow merge commits and squash merging

## Best Practices

### For Developers

1. **Run tests locally before pushing**:
   ```bash
   uv run pytest
   ```

2. **Check code quality locally**:
   ```bash
   uv run ruff check src/ tests/
   uv run mypy src/
   ```

3. **Format code before committing**:
   ```bash
   uv run ruff format src/ tests/
   ```

4. **Test Docker build locally**:
   ```bash
   docker build -t ai-ea:local .
   ```

### For CI/CD

1. Keep workflow files DRY using reusable workflows
2. Use caching aggressively for speed
3. Fail fast on critical errors
4. Always run smoke tests after deployment
5. Monitor deployment metrics

## Performance Optimization

### Caching Strategy
- **uv dependencies**: ~/.cache/uv
- **Docker layers**: Docker buildx cache
- **Mypy cache**: .mypy_cache/
- **Ruff cache**: .ruff_cache/

### Parallel Execution
- Run independent jobs in parallel
- Use matrix strategy for multi-version testing
- Concurrent Docker builds for different platforms

### Resource Management
- Set appropriate timeouts (15 min for tests)
- Use smaller runner images when possible
- Clean up artifacts after retention period

## Monitoring and Alerts

### Metrics Tracked
- Build success/failure rate
- Test execution time
- Code coverage trends
- Deployment frequency
- Mean time to recovery (MTTR)

### Alerts
- Failed deployments → Slack + Email
- Security vulnerabilities found → GitHub Security
- Test failures on main → GitHub notifications
- Low code coverage → PR annotations

## Troubleshooting

### Common Issues

**Tests failing in CI but passing locally**:
- Check environment variables
- Verify database service is running
- Check Python version matches

**Docker build failures**:
- Clear Docker cache
- Check .dockerignore is correct
- Verify all dependencies are in pyproject.toml

**Deployment failures**:
- Check health endpoint
- Review deployment logs
- Verify secrets are configured
- Check database migration status

### Debug Commands

```bash
# Run CI locally with act
act -j test

# Debug Docker build
docker build --progress=plain -t ai-ea:debug .

# Test deployment script
./scripts/deploy.sh --dry-run
```

## Future Enhancements

1. **Advanced Testing**:
   - Visual regression testing
   - Performance benchmarking
   - Load testing in CI

2. **Enhanced Security**:
   - SAST (Static Application Security Testing)
   - Dependency scanning with Dependabot
   - Secret scanning

3. **Deployment Improvements**:
   - Blue-green deployments
   - Canary deployments
   - A/B testing infrastructure

4. **Observability**:
   - APM (Application Performance Monitoring)
   - Distributed tracing
   - Log aggregation

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Field Manual](../plan.md#uv-field-manual)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Deployment Guide](./deployment.md) (to be created in Step 35)
