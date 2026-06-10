# ABOUTME: Standardized API response envelope and supporting models
# ABOUTME: Every response carries success flag, data or error, request ID, and timestamp

from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error payload."""

    code: Annotated[str, Field(description="Stable machine-readable error code")]
    message: Annotated[str, Field(description="Human-readable error message")]
    details: Annotated[
        dict[str, Any] | None, Field(description="Optional structured error context")
    ] = None


class StandardResponse(BaseModel):
    """Envelope for all API responses."""

    success: Annotated[bool, Field(description="Whether the request succeeded")]
    data: Annotated[Any | None, Field(description="Response payload on success")] = None
    error: Annotated[ErrorDetail | None, Field(description="Error payload on failure")] = None
    request_id: Annotated[str, Field(description="Correlation ID for tracing")]
    timestamp: Annotated[datetime, Field(description="Server time of the response")] = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class PaginatedData(BaseModel):
    """Payload shape for paginated list responses."""

    items: Annotated[list[Any], Field(description="Items on this page")]
    total: Annotated[int, Field(ge=0, description="Total items across all pages")]
    limit: Annotated[int, Field(gt=0, description="Page size requested")]
    offset: Annotated[int, Field(ge=0, description="Items skipped before this page")]


def success_response(data: Any, request_id: str) -> StandardResponse:
    """Build a success envelope."""
    return StandardResponse(success=True, data=data, request_id=request_id)


def error_response(error: ErrorDetail, request_id: str) -> StandardResponse:
    """Build an error envelope."""
    return StandardResponse(success=False, error=error, request_id=request_id)
