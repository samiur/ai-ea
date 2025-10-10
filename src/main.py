# ABOUTME: Main FastAPI application entry point
# ABOUTME: Configures app, middleware, and core endpoints

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown events."""
    # Startup
    print("🚀 Starting AI Executive Assistant API...")
    yield
    # Shutdown
    print("👋 Shutting down AI Executive Assistant API...")


# Create FastAPI application
app = FastAPI(
    title="AI Executive Assistant",
    description="AI-powered executive assistant for calendar management and coordination",
    version="0.1.0",
    lifespan=lifespan,
)

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


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/status")
async def status() -> dict[str, str]:
    """Status endpoint returning app information."""
    return {
        "app_name": "AI Executive Assistant",
        "version": "0.1.0",
        "environment": "development",
    }
