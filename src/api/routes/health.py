# ABOUTME: Health check endpoints, basic and detailed
# ABOUTME: Detailed check queries the database; redis mocked until the queue lands

from typing import Any

from fastapi import APIRouter

from src.database import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check. Contract: exactly {"status": "healthy"}."""
    return {"status": "healthy"}


@router.get("/health/detailed")
async def health_detailed() -> dict[str, Any]:
    """Readiness-style check reporting per-dependency status.

    Redis reports "mocked" until the queue is introduced.
    """
    db_up = await check_database_connection()

    checks: dict[str, dict[str, str]] = {
        "database": {"status": "up" if db_up else "down"},
        "redis": {"status": "mocked"},
        "external_services": {"status": "not_configured"},
    }
    return {
        "status": "healthy" if db_up else "degraded",
        "checks": checks,
    }
