# ABOUTME: Global exception handlers mapping errors to the standard response envelope
# ABOUTME: Logs server errors with request context and sanitizes messages in production

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.errors import APIError
from src.api.responses import ErrorDetail, error_response
from src.config import get_settings

logger = logging.getLogger("ai_ea.errors")


def _request_id(request: Request) -> str:
    """Get the correlation ID set by the request-ID middleware."""
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else "unknown"


def _envelope(request: Request, status_code: int, detail: ErrorDetail) -> JSONResponse:
    """Render an error envelope as a JSON response."""
    payload = error_response(detail, request_id=_request_id(request))
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_error_handlers(app: FastAPI) -> None:
    """Attach the global exception handlers to an application."""

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("API error: %s", exc.message, extra={"request_id": _request_id(request)})
        return _envelope(
            request,
            exc.status_code,
            ErrorDetail(code=exc.error_code, message=exc.message, details=exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details: dict[str, Any] = {"errors": exc.errors()}
        return _envelope(
            request,
            422,
            ErrorDetail(
                code="validation_error", message="Request validation failed", details=details
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _envelope(
            request,
            exc.status_code,
            ErrorDetail(code="http_error", message=str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id(request)
        logger.exception("Unhandled error (request_id=%s): %s", request_id, exc)

        if get_settings().environment == "production":
            message = "An internal error occurred"
        else:
            message = f"{type(exc).__name__}: {exc}"
        return _envelope(request, 500, ErrorDetail(code="internal_error", message=message))
