# Repository Secrets Configuration

This document outlines all required GitHub repository secrets for the AI Executive Assistant project's CI/CD pipeline.

## Required Secrets

The following secrets must be configured in the GitHub repository settings (`Settings > Secrets and variables > Actions`).

### Development & Testing

#### `DATABASE_URL`
- **Purpose**: PostgreSQL connection string for integration tests
- **Format**: `postgresql://user:password@host:port/database`
- **Example**: `postgresql://test_user:test_pass@localhost:5432/test_db`
- **Required for**: Test execution in CI (Step 5)
- **Notes**: The CI workflow automatically provisions a PostgreSQL 15 service container, so this should point to that container

### Google Integration

#### `GOOGLE_CLIENT_ID`
- **Purpose**: OAuth 2.0 client ID for Google Calendar and Gmail API access
- **Format**: String (from Google Cloud Console)
- **Example**: `123456789-abcdefg.apps.googleusercontent.com`
- **Required for**: Integration tests for Google Calendar/Gmail features (Steps 16-22)
- **Setup**:
  1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
  2. Enable Calendar API and Gmail API
  3. Create OAuth 2.0 credentials
  4. Copy the Client ID

#### `GOOGLE_CLIENT_SECRET`
- **Purpose**: OAuth 2.0 client secret for Google API access
- **Format**: String (from Google Cloud Console)
- **Example**: `GOCSPX-xxxxxxxxxxxxxxxxxxxxx`
- **Required for**: Integration tests for Google Calendar/Gmail features (Steps 16-22)
- **Setup**: Available in the same OAuth credentials page as the Client ID
- **Security**: This is a sensitive credential - never commit to git

### Slack Integration

#### `SLACK_BOT_TOKEN`
- **Purpose**: Bot User OAuth Token for Slack Bot API access
- **Format**: String starting with `xoxb-`
- **Example**: `xoxb-YOUR-WORKSPACE-ID-YOUR-BOT-ID-YOUR-TOKEN-HERE`
- **Required for**: Integration tests for Slack messaging features (Steps 24-25)
- **Setup**:
  1. Create a Slack app at [api.slack.com](https://api.slack.com/apps)
  2. Add bot scopes: `chat:write`, `im:write`, `channels:read`
  3. Install app to workspace
  4. Copy the Bot User OAuth Token
- **Security**: This token provides full bot access - protect it carefully

#### `SLACK_SIGNING_SECRET`
- **Purpose**: Verify incoming requests from Slack are authentic
- **Format**: String (32-character hex string)
- **Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`
- **Required for**: Slack webhook verification (Step 25)
- **Setup**: Available in the Slack app's "Basic Information" page under "App Credentials"

## Optional Secrets (Future Steps)

The following secrets will be needed for later implementation steps but are not required for Steps 1-8:

### Deployment

- `DOCKER_REGISTRY_TOKEN` - For pushing Docker images to container registry (Step 7)
- `DEPLOY_SSH_KEY` - For SSH access to deployment servers (Step 8)
- `PRODUCTION_DATABASE_URL` - Production PostgreSQL connection string (Step 8)
- `REDIS_URL` - Redis connection string for production (Future)

### External Services

- `ZEP_API_KEY` - For Zep memory graph integration (Future)
- `OPENAI_API_KEY` - For LLM processing (Future)

## Setting Up Secrets

### In GitHub

1. Navigate to repository: https://github.com/samiur/ai-ea
2. Go to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Enter the secret name and value
5. Click **Add secret**

### Local Development

For local development, these values should be stored in a `.env` file (never committed):

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual values
# These are used when running tests locally
```

Example `.env` file structure:
```env
# Database
DATABASE_URL=postgresql://assistant:assistant@localhost:5432/ai_assistant

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Application
SECRET_KEY=your-secret-key-for-jwt
ENVIRONMENT=development
DEBUG=true
```

## Security Best Practices

1. **Never commit secrets to git** - Always use environment variables or secrets management
2. **Rotate secrets regularly** - Especially after any suspected compromise
3. **Use separate secrets for each environment** - Don't reuse production secrets in development
4. **Limit secret access** - Only grant access to team members who need it
5. **Monitor secret usage** - Review GitHub Actions logs for unauthorized access attempts

## Verification

To verify all required secrets are configured for the current step (Step 4):

```bash
# Check that tests pass locally with secrets from .env
uv run pytest tests/test_ci_setup.py

# Check that secrets are documented
grep -E "GOOGLE_CLIENT_ID|GOOGLE_CLIENT_SECRET|SLACK_BOT_TOKEN|DATABASE_URL" docs/secrets.md
```

The CI workflow will fail with clear error messages if required secrets are missing.

## Troubleshooting

### "Secret not found" error in CI
- Verify the secret name exactly matches (case-sensitive)
- Check that the secret is set at the repository level, not organization level
- Ensure the secret has a value (not empty)

### Google OAuth errors
- Verify the Client ID and Secret match your Google Cloud Console project
- Check that Calendar API and Gmail API are enabled
- Ensure redirect URIs are configured correctly

### Slack verification failures
- Verify the signing secret matches your Slack app
- Check that the bot token has required scopes
- Ensure the app is installed to the workspace

## References

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Google OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)
- [Slack App Configuration](https://api.slack.com/authentication/basics)
