# ABOUTME: Main FastAPI application entry point
# ABOUTME: Configures app, middleware, and core endpoints

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.config import get_settings
from src.database import dispose_engine, init_db
from src.middleware.error_handler import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown events."""
    settings = get_settings()

    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.version}...")
    print(f"📦 Environment: {settings.environment}")
    print(f"🐛 Debug mode: {settings.debug}")

    # Validate settings on startup
    if settings.environment == "production" and settings.debug:
        print("⚠️  WARNING: Debug mode is enabled in production!")

    # Initialize database (non-fatal in dev; /health/detailed reports state)
    try:
        await init_db()
        print("🗄️  Database initialized")
    except Exception as exc:
        print(f"⚠️  Database unavailable at startup: {exc}")

    yield

    # Shutdown
    await dispose_engine()
    print(f"👋 Shutting down {settings.app_name}...")


# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered executive assistant for calendar management and coordination",
    version=settings.version,
    lifespan=lifespan,
    debug=settings.debug,
)

# Standardized error envelopes for all exceptions
register_error_handlers(app)

# Health endpoints (basic + detailed dependency checks)
app.include_router(health_router)

# Configure CORS for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning welcome message and API documentation link."""
    return {
        "message": "Welcome to AI Executive Assistant API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/status")
async def status() -> dict[str, str]:
    """Status endpoint returning app information."""
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }
