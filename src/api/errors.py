# ABOUTME: Custom exception hierarchy for the API
# ABOUTME: Each error maps to an HTTP status code and a stable machine-readable code

from typing import Any


class APIError(Exception):
    """Base class for all API errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(APIError):
    """Requested resource does not exist."""

    status_code = 404
    error_code = "not_found"


class ValidationError(APIError):
    """Request payload or parameters failed domain validation."""

    status_code = 400
    error_code = "validation_error"


class AuthenticationError(APIError):
    """Caller identity could not be established."""

    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(APIError):
    """Caller is authenticated but not permitted to do this."""

    status_code = 403
    error_code = "authorization_error"


class ConflictError(APIError):
    """Request conflicts with current resource state."""

    status_code = 409
    error_code = "conflict"


class ExternalServiceError(APIError):
    """An upstream dependency (Google, Slack, ...) failed."""

    status_code = 503
    error_code = "external_service_error"
