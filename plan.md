# AI Executive Assistant - Implementation Plan

## Project Overview
Building an AI-powered executive assistant for calendar management and coordination, focusing on:
- Automatic rescheduling of 1-1s based on priority conflicts
- Finding time for new meetings across Google Calendar, Gmail, and Slack
- Policy-driven decision making with approval workflows
- Learning preferences via Zep memory graph

## Technical Stack
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with SQLModel ORM
- **Queue**: Redis with RQ
- **Memory**: Zep for preference learning
- **Integrations**: Google Calendar/Gmail APIs, Slack Bot
- **Testing**: Pytest, Playwright for integration tests
- **Package Management**: uv

## Implementation Phases

> **Note**: CI/CD infrastructure (Steps 4-8) has been moved early in the implementation plan to provide immediate quality feedback and automated testing from the start. See `docs/step-reorganization.md` for details.

### Phase 1: Foundation & CI/CD (Steps 1-10)
Basic project setup, **CI/CD pipeline** (Steps 4-8), database, and API structure

### Phase 2: Database & Models (Steps 11-17)
Database setup, core models, repository pattern, and feature flags

### Phase 3: Authentication & Security (Steps 18-20)
OAuth configuration, secure token storage, and JWT middleware

### Phase 4: Google Integration (Steps 21-25)
Google OAuth, Calendar API, conflict detection, and Gmail integration

### Phase 5: Communication (Steps 26-32)
Slack bot, message templates, draft generation, and email parsing

### Phase 6: Orchestration (Steps 33-35)
Scheduler, approval workflows, and orchestrator

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

### Step 4: Docker Compose for PostgreSQL

```text
Set up PostgreSQL with Docker Compose for local development.

Building on Steps 1-3:

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

### Step 5: SQLModel Setup and Connection

```text
Configure SQLModel ORM and database connection management.

Building on Steps 1-4:

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

### Step 6: Person and Policy Data Models

```text
Create Person and Policy data models with full CRUD operations.

Building on Steps 1-5:

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

### Step 7: Meeting Series and Related Models

```text
Implement MeetingSeries and related scheduling models.

Building on Steps 1-6:

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

### Step 8: Database Migrations with Alembic

```text
Set up Alembic for database migrations and create initial schema.

Building on Steps 1-7:

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

7. Document migration workflow in README

Ensure migrations work up and down cleanly.
```

### Step 9: Repository Pattern Implementation

```text
Implement a clean repository pattern for data access.

Building on Steps 1-8:

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
     - Database connectivity
     - Redis connectivity (mock for now)
     - External service status

Ensure consistent error handling across all endpoints.
```

### Step 11: Feature Flags System

```text
Implement a feature flag system for gradual rollout and configuration.

Building on Steps 1-10:

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

### Step 12: Policy YAML Loader and Parser

```text
Create a system to load and parse policy configurations from YAML/JSON.

Building on Steps 1-11:

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

### Step 13: OAuth Configuration Models

```text
Design OAuth configuration models for Google and Slack integrations.

Building on Steps 1-12:

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

### Step 14: Secure Token Storage

```text
Implement secure token storage with encryption and key management.

Building on Steps 1-13:

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

### Step 15: JWT Middleware for Internal APIs

```text
Implement JWT authentication middleware for internal API security.

Building on Steps 1-14:

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

### Step 16: Google OAuth Credential Setup

```text
Implement Google OAuth flow for Calendar and Gmail access.

Building on Steps 1-15:

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
   - Group scopes by feature

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

### Step 17: Google Calendar API Client

```text
Create a Google Calendar API client wrapper with common operations.

Building on Steps 1-16:

1. Write tests in tests/test_google_calendar.py:
   - Test calendar list retrieval
   - Test event fetching
   - Test free/busy queries
   - Test error handling
   - Mock API responses

2. Install google-api-python-client:
   - Add to dependencies via uv

3. Create src/integrations/google/calendar.py:
   - GoogleCalendarClient class:
     - __init__(credentials: OAuthCredential)
     - list_calendars() -> List[Calendar]
     - get_events(calendar_id, time_min, time_max)
     - get_event(calendar_id, event_id)
     - get_freebusy(time_min, time_max, calendars)
   - Handle pagination
   - Implement retry logic
   - Rate limiting awareness

4. Create src/schemas/calendar.py:
   - Pydantic models:
     - Calendar
     - Event
     - Attendee
     - FreeBusySlot
     - TimeSlot

5. Create src/services/calendar_service.py:
   - CalendarService wrapper:
     - get_user_calendars(user_id)
     - fetch_events_range(user_id, start, end)
     - check_availability(user_id, slots)
   - Cache calendar data
   - Handle multiple calendars

6. Add calendar endpoints:
   - GET /calendars - list user calendars
   - GET /calendars/{id}/events - get events
   - POST /calendars/freebusy - check availability

Ensure proper error handling and rate limit management.
```

### Step 18: Fetch Calendar Events (Read-Only)

```text
Implement calendar event fetching with proper data transformation.

Building on Steps 1-17:

1. Write tests in tests/test_event_fetching.py:
   - Test single event fetch
   - Test recurring event expansion
   - Test all-day event handling
   - Test timezone conversion

2. Enhance GoogleCalendarClient:
   - fetch_events_detailed(calendar_id, params)
   - expand_recurring_events(event, start, end)
   - get_event_instances(calendar_id, event_id)
   - Handle various event types

3. Create src/services/event_processor.py:
   - EventProcessor class:
     - process_raw_event(google_event) -> Event
     - extract_attendees(google_event) -> List[Attendee]
     - parse_recurrence_rule(rrule_string)
     - normalize_timezone(dt, from_tz, to_tz)
     - detect_event_type(event) -> EventType

4. Create src/models/calendar_event.py:
   - CalendarEvent model (cache):
     - event_id: str (Google ID)
     - calendar_id: str
     - user_id: UUID
     - title: str
     - start_time: datetime
     - end_time: datetime
     - is_recurring: bool
     - attendees: JSON
     - last_synced: datetime

5. Create sync mechanism:
   - Incremental sync with sync tokens
   - Handle deleted events
   - Track modification times

6. Add event query endpoints:
   - GET /events/today
   - GET /events/week
   - GET /events/conflicts

Test with various calendar configurations.
```

### Step 19: Free/Busy Time Retrieval

```text
Implement free/busy time checking for scheduling decisions.

Building on Steps 1-18:

1. Write tests in tests/test_freebusy.py:
   - Test free/busy API calls
   - Test slot availability checking
   - Test multiple calendar merge
   - Test working hours overlay

2. Enhance calendar client:
   - batch_freebusy_query(emails, time_min, time_max)
   - parse_freebusy_response(response)
   - merge_busy_times(busy_lists)

3. Create src/services/availability_service.py:
   - AvailabilityService class:
     - get_busy_slots(user_id, start, end)
     - find_free_slots(user_id, duration, range)
     - check_slot_availability(user_id, slot)
     - get_working_hours(user_id, date)
     - apply_buffer_time(slots, before, after)

4. Create src/utils/time_utils.py:
   - Slot manipulation utilities:
     - merge_overlapping_slots(slots)
     - subtract_slots(available, busy)
     - split_slot_by_duration(slot, duration)
     - align_to_time_grid(slot, grid_minutes)

5. Create src/schemas/availability.py:
   - AvailabilityRequest model
   - AvailabilityResponse model
   - BusySlot model
   - FreeSlot model

6. Add availability endpoints:
   - POST /availability/check
   - POST /availability/find-slots
   - GET /availability/working-hours

Ensure accurate availability calculation.
```

### Step 20: Basic Conflict Detection Logic

```text
Build conflict detection system for calendar events.

Building on Steps 1-19:

1. Write comprehensive tests in tests/test_conflict_detection.py:
   - Test overlapping events
   - Test buffer time conflicts
   - Test priority comparison
   - Test recurring event conflicts

2. Create src/services/conflict_detector.py:
   - ConflictDetector class:
     - detect_conflicts(events) -> List[Conflict]
     - check_event_overlap(event1, event2)
     - evaluate_conflict_severity(conflict)
     - get_resolution_suggestions(conflict)
     - monitor_calendar_changes(user_id)

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

4. Create src/services/conflict_resolver.py:
   - ConflictResolver class:
     - suggest_resolution(conflict)
     - can_reschedule(event, policy)
     - find_alternative_slots(event)
     - prioritize_events(events)

5. Add background job for conflict monitoring:
   - Periodic calendar scan
   - Real-time webhook processing
   - Notification generation

6. Add conflict endpoints:
   - GET /conflicts/active
   - POST /conflicts/resolve/{id}
   - GET /conflicts/suggestions/{id}

Test with various conflict scenarios.
```

### Step 21: Gmail API Client Setup

```text
Set up Gmail API client for email integration.

Building on Steps 1-20:

1. Write tests in tests/test_gmail_client.py:
   - Test Gmail authentication
   - Test message listing
   - Test thread retrieval
   - Test draft creation

2. Create src/integrations/google/gmail.py:
   - GmailClient class:
     - list_messages(query, max_results)
     - get_message(message_id)
     - get_thread(thread_id)
     - create_draft(message)
     - send_message(message)
     - add_label(message_id, label)

3. Create src/schemas/email.py:
   - Email models:
     - EmailMessage
     - EmailThread
     - EmailDraft
     - EmailAddress
     - EmailAttachment

4. Create src/services/email_service.py:
   - EmailService wrapper:
     - fetch_recent_threads(user_id)
     - search_emails(user_id, query)
     - get_thread_context(thread_id)
     - extract_participants(thread)

5. Add Gmail-specific settings:
   - gmail_label_prefix: "AI-Assistant"
   - gmail_watch_labels: ["INBOX"]

6. Create email endpoints:
   - GET /emails/threads
   - GET /emails/threads/{id}
   - POST /emails/search

Ensure proper Gmail API error handling.
```

### Step 22: Email Thread Reader

```text
Implement email thread reading and context extraction.

Building on Steps 1-21:

1. Write tests in tests/test_email_reader.py:
   - Test thread parsing
   - Test message ordering
   - Test participant extraction
   - Test quoted text detection

2. Create src/services/email_reader.py:
   - EmailReader class:
     - read_thread(thread_id) -> ThreadContext
     - extract_latest_message(thread)
     - get_sender_info(message)
     - extract_message_body(message)
     - detect_quoted_text(body)
     - extract_signatures(body)

3. Create src/utils/email_parser.py:
   - Email parsing utilities:
     - parse_html_body(html) -> str
     - extract_plain_text(message)
     - clean_email_content(text)
     - detect_language(text)
     - extract_action_items(text)

4. Create src/schemas/thread_context.py:
   - ThreadContext model:
     - thread_id: str
     - subject: str
     - participants: List[EmailAddress]
     - latest_message: str
     - message_count: int
     - has_attachments: bool

5. Implement smart truncation:
   - Keep recent context
   - Remove repetitive quotes
   - Preserve key information

6. Add thread analysis endpoint:
   - POST /emails/analyze-thread

Test with various email formats and clients.
```

### Step 23: Meeting Request Parser

```text
Parse meeting requests from email content.

Building on Steps 1-22:

1. Write tests in tests/test_meeting_parser.py:
   - Test meeting request detection
   - Test time extraction
   - Test attendee parsing
   - Test duration detection

2. Create src/services/meeting_parser.py:
   - MeetingRequestParser class:
     - parse_email_for_meeting(email_content)
     - extract_meeting_times(text)
     - extract_duration(text)
     - extract_attendees(text, context)
     - extract_meeting_purpose(text)
     - confidence_score(extracted_data)

3. Create src/utils/nlp_helpers.py:
   - NLP utilities:
     - extract_dates_times(text)
     - parse_relative_time(phrase)
     - extract_email_addresses(text)
     - detect_meeting_keywords(text)
     - extract_timezone_hints(text)

4. Create src/schemas/meeting_request.py:
   - MeetingRequest model:
     - requested_times: List[TimeSlot]
     - duration_minutes: int
     - attendees: List[str]
     - purpose: str
     - urgency: Enum
     - confidence: float

5. Use dateutil and regex for parsing:
   - Handle various date formats
   - Support relative times
   - Detect recurring patterns

6. Add parsing endpoint:
   - POST /meetings/parse-request

Test with various meeting request formats.
```

### Step 24: Slack App Configuration

```text
Set up Slack bot application with proper configuration.

Building on Steps 1-23:

1. Write tests in tests/test_slack_setup.py:
   - Test Slack client initialization
   - Test bot token validation
   - Test event signature verification
   - Test rate limiting

2. Create src/integrations/slack/__init__.py

3. Create src/integrations/slack/client.py:
   - SlackClient wrapper class:
     - __init__(bot_token, signing_secret)
     - verify_signature(request)
     - send_message(channel, text, blocks)
     - send_dm(user_id, text)
     - reply_to_thread(channel, thread_ts, text)
     - get_user_info(user_id)

4. Create src/integrations/slack/config.py:
   - Slack configuration:
     - Required scopes
     - Event subscriptions
     - Slash commands
     - Interactive components

5. Create Slack app manifest (slack-app-manifest.yml):
   - Define bot scopes
   - Set up event subscriptions
   - Configure slash commands
   - Add interactive components

6. Add Slack settings to config:
   - slack_bot_token
   - slack_signing_secret
   - slack_app_id
   - slack_team_id

7. Create setup documentation:
   - Slack app creation steps
   - OAuth setup
   - Event URL configuration

Test Slack client initialization.
```

### Step 25: Slack Event Handler

```text
Implement Slack event handling and message processing.

Building on Steps 1-24:

1. Write tests in tests/test_slack_events.py:
   - Test event routing
   - Test message events
   - Test app mentions
   - Test DM handling
   - Test thread responses

2. Create src/integrations/slack/events.py:
   - SlackEventHandler class:
     - handle_event(event_data)
     - handle_message(event)
     - handle_app_mention(event)
     - handle_reaction(event)
     - handle_slash_command(command)

3. Create src/api/routes/slack.py:
   - POST /slack/events - event webhook
   - POST /slack/slash - slash commands
   - POST /slack/interactive - button/select actions
   - Implement URL verification

4. Create src/services/slack_processor.py:
   - SlackMessageProcessor:
     - process_message(text, user_id, channel)
     - detect_intent(message)
     - extract_mentions(text)
     - format_response(response_data)

5. Implement rate limiting:
   - Track API calls
   - Implement backoff
   - Queue messages if needed

6. Add Slack-specific models:
   - SlackMessage
   - SlackUser
   - SlackChannel

7. Create message queue for async processing

Test full event flow from Slack.
```

### Step 26: Message Template Engine

```text
Build a flexible message template system using Jinja2.

Building on Steps 1-25:

1. Write tests in tests/test_templates.py:
   - Test template rendering
   - Test variable substitution
   - Test conditional blocks
   - Test template inheritance

2. Add jinja2 to dependencies via uv

3. Create templates directory structure:
   ```
   templates/
     email/
       reschedule_request.html
       reschedule_request.txt
       meeting_request.html
     slack/
       reschedule_dm.json
       approval_blocks.json
     base/
       email_base.html
   ```

4. Create src/services/template_engine.py:
   - TemplateEngine class:
     - render_template(name, context)
     - render_email(template, context)
     - render_slack_blocks(template, context)
     - register_custom_filters()
     - validate_template(template)

5. Create sample templates:
   - Reschedule notification
   - Meeting request
   - Approval request
   - Confirmation message

6. Create src/utils/template_helpers.py:
   - Custom Jinja filters:
     - format_datetime(dt, tz)
     - format_duration(minutes)
     - format_attendee_list(attendees)
     - escape_slack_text(text)

7. Add template management:
   - Template versioning
   - A/B testing support
   - Template preview endpoint

Test template rendering with various contexts.
```

### Step 27: Draft Message Generator

```text
Generate draft messages for email and Slack communications.

Building on Steps 1-26:

1. Write tests in tests/test_draft_generator.py:
   - Test email draft generation
   - Test Slack message generation
   - Test tone adaptation
   - Test context inclusion

2. Create src/services/draft_generator.py:
   - DraftGenerator class:
     - generate_email_draft(intent, context)
     - generate_slack_message(intent, context)
     - select_template(intent_type, channel)
     - apply_tone(message, tone_preference)
     - include_agenda_items(message, items)

3. Create src/schemas/draft.py:
   - Draft models:
     - EmailDraft
     - SlackDraft
     - DraftMetadata
     - TonePreference

4. Create tone configurations:
   - Executive (concise, formal)
   - Internal (friendly, casual)
   - Customer (professional, detailed)
   - Urgent (direct, action-oriented)

5. Implement smart context inclusion:
   - Previous message context
   - Meeting history
   - Participant preferences
   - Time zone awareness

6. Add draft endpoints:
   - POST /drafts/email
   - POST /drafts/slack
   - PUT /drafts/{id}/edit
   - POST /drafts/{id}/send

Test various draft scenarios.
```

### Step 28: Scheduler Slot Finder

```text
Implement intelligent slot-finding algorithm for meetings.

Building on Steps 1-27:

1. Write comprehensive tests in tests/test_slot_finder.py:
   - Test slot finding algorithm
   - Test constraint satisfaction
   - Test preference weighting
   - Test multiple attendee coordination

2. Create src/services/scheduler.py:
   - Scheduler class:
     - find_available_slots(request) -> List[TimeSlot]
     - rank_slots(slots, preferences)
     - check_constraints(slot, constraints)
     - optimize_for_preferences(slots)
     - handle_timezone_complexity(slots, attendees)

3. Create src/algorithms/slot_finder.py:
   - SlotFindingAlgorithm:
     - find_common_availability(attendees, range)
     - apply_working_hours(slots, person)
     - apply_buffer_times(slots, policy)
     - detect_back_to_back(slots)
     - score_slot_quality(slot)

4. Create src/models/constraints.py:
   - Constraint models:
     - TimeConstraint
     - DurationConstraint
     - AttendeeConstraint
     - LocationConstraint

5. Implement optimization strategies:
   - Minimize time zone pain
   - Preserve focus blocks
   - Maintain meeting cadence
   - Balance calendar density

6. Add scheduler endpoints:
   - POST /scheduler/find-slots
   - POST /scheduler/evaluate-slot
   - GET /scheduler/suggestions

Test with complex scheduling scenarios.
```

### Step 29: Approval Workflow Models

```text
Create approval workflow system for scheduling decisions.

Building on Steps 1-28:

1. Write tests in tests/test_approval_workflow.py:
   - Test approval creation
   - Test approval states
   - Test timeout handling
   - Test auto-approval logic

2. Create src/models/approval.py:
   - Approval model:
     - approval_id: UUID
     - decision_id: UUID
     - status: Enum["pending", "approved", "rejected", "timeout"]
     - created_at: datetime
     - expires_at: datetime
     - approved_by: Optional[UUID]
     - approval_method: Enum["manual", "auto", "timeout_default"]

3. Create src/services/approval_service.py:
   - ApprovalService class:
     - create_approval(decision, timeout_minutes)
     - process_approval(approval_id, action)
     - check_auto_approval(decision)
     - handle_timeout(approval_id)
     - get_pending_approvals(user_id)

4. Create src/schemas/approval.py:
   - Approval request/response models
   - ApprovalCard for Slack/email
   - ApprovalContext

5. Implement approval UI components:
   - Slack interactive blocks
   - Email action buttons
   - Web approval page

6. Add approval endpoints:
   - GET /approvals/pending
   - POST /approvals/{id}/approve
   - POST /approvals/{id}/reject
   - GET /approvals/{id}/status

7. Create timeout handler job

Test full approval lifecycle.
```

### Step 30: Basic Orchestrator with State Machine

```text
Build the core orchestrator that coordinates all components.

Building on Steps 1-29:

1. Write tests in tests/test_orchestrator.py:
   - Test state transitions
   - Test workflow execution
   - Test error recovery
   - Test rollback scenarios

2. Create src/services/orchestrator.py:
   - Orchestrator class:
     - process_intent(intent) -> Decision
     - execute_decision(decision)
     - handle_state_transition(from_state, to_state)
     - coordinate_services(intent, context)
     - handle_failure(error, state)

3. Create src/models/workflow_state.py:
   - WorkflowState enum:
     - INTENT_CREATED
     - ANALYZING
     - AWAITING_APPROVAL
     - APPROVED
     - EXECUTING
     - COMPLETED
     - FAILED

4. Create src/services/workflow_engine.py:
   - WorkflowEngine class:
     - State machine implementation
     - Transition rules
     - State persistence
     - Retry logic
     - Compensation actions

5. Implement core workflows:
   - Reschedule 1-on-1
   - New meeting request
   - Conflict resolution
   - Hold management

6. Create src/services/context_builder.py:
   - Build context for decisions
   - Aggregate data from services
   - Cache context data

7. Add orchestrator endpoints:
   - POST /workflows/start
   - GET /workflows/{id}/status
   - POST /workflows/{id}/retry

8. Implement basic monitoring:
   - Log state transitions
   - Track execution time
   - Record decision rationale

Test end-to-end workflow execution.
```

---

## Phase 6: CI/CD Infrastructure (Steps 31-35)

### Step 31: Basic GitHub Actions Workflow

```text
Set up foundational GitHub Actions workflow for CI/CD.

Building on Steps 1-30:

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

### Step 32: Test Execution in CI

```text
Implement comprehensive test execution in GitHub Actions.

Building on Steps 1-31:

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

### Step 33: Code Quality Checks

```text
Add comprehensive code quality checks to CI pipeline.

Building on Steps 1-32:

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

### Step 34: Docker Build and Registry

```text
Add Docker image building and registry push to CI/CD pipeline.

Building on Steps 1-33:

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
   COPY alembic/ ./alembic/
   COPY alembic.ini ./

   # Expose port
   EXPOSE 8000

   # Run migrations and start app
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

### Step 35: Deployment Automation

```text
Implement automated deployment workflows for staging and production.

Building on Steps 1-34:

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

---

## Testing Strategy

Each step includes:
1. **Unit tests** - Test individual components
2. **Integration tests** - Test component interactions
3. **E2E tests** - Test full user scenarios (from Step 20+)

## Deployment Strategy

1. Local development with Docker Compose
2. CI/CD with GitHub Actions (See Steps 31-35 for implementation)
3. Staging environment on Vercel/Railway
4. Production deployment with monitoring

## Next Steps After MVP

1. CI/CD Infrastructure (Steps 31-35)
2. Zep memory integration (Steps 36-40)
3. Confidence scoring and ML (Steps 41-45)
4. Advanced features (travel mode, sanity sweeps)
5. Performance optimization
6. Production hardening

## Success Criteria

- All tests passing (unit, integration, E2E)
- Core workflows functioning end-to-end
- Approval workflow operational
- Basic calendar operations working
- Email/Slack communication functional
- Policy engine evaluating correctly

## Risk Mitigation

- Each step is independently testable
- No step breaks previous functionality
- Gradual complexity increase
- Feature flags for risky features
- Comprehensive error handling at each layer