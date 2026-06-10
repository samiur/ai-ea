# ABOUTME: Health check endpoints, basic and detailed
# ABOUTME: Detailed check probes dependencies (database TCP; redis mocked until the queue lands)

import asyncio
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter

from src.config import get_settings

router = APIRouter(tags=["health"])


async def _tcp_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check whether a TCP endpoint accepts connections."""
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    except (TimeoutError, OSError):
        return False
    writer.close()
    await writer.wait_closed()
    return True


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check. Contract: exactly {"status": "healthy"}."""
    return {"status": "healthy"}


@router.get("/health/detailed")
async def health_detailed() -> dict[str, Any]:
    """Readiness-style check reporting per-dependency status.

    Database is probed via plain TCP — no DB driver is a dependency until
    Step 11. Redis reports "mocked" until the queue is introduced.
    """
    settings = get_settings()
    db_url = urlparse(settings.database_url)
    db_up = await _tcp_reachable(db_url.hostname or "localhost", db_url.port or 5432)

    checks: dict[str, dict[str, str]] = {
        "database": {"status": "up" if db_up else "down"},
        "redis": {"status": "mocked"},
        "external_services": {"status": "not_configured"},
    }
    return {
        "status": "healthy" if db_up else "degraded",
        "checks": checks,
    }
