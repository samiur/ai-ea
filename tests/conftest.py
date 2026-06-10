# ABOUTME: Shared pytest configuration for the test suite
# ABOUTME: Provides required settings env vars so tests run standalone and in any order

import os

# Required Settings fields. setdefault keeps real values (e.g., CI's
# DATABASE_URL pointing at the postgres service container) when present.
os.environ.setdefault(
    "DATABASE_URL", "postgresql://assistant:assistant@localhost:5432/ai_assistant"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long!!")
