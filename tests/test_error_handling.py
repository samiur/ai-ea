# ABOUTME: Tests for API error handling and standardized responses (Step 10)
# ABOUTME: Covers error classes, response envelope, handler registration, and health checks

import logging
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.errors import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from src.api.responses import ErrorDetail, PaginatedData, success_response
from src.middleware.error_handler import register_error_handlers


@pytest.fixture
def app() -> FastAPI:
    """A minimal app with error handlers and routes that raise each error."""
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/boom/{error_name}")
    async def boom(error_name: str) -> dict[str, str]:
        errors: dict[str, APIError] = {
            "not_found": NotFoundError("Thing not found"),
            "validation": ValidationError("Bad input"),
            "authentication": AuthenticationError("Who are you?"),
            "authorization": AuthorizationError("Not allowed"),
            "conflict": ConflictError("Already exists"),
            "external": ExternalServiceError("Google is down"),
        }
        raise errors[error_name]

    @test_app.get("/unhandled")
    async def unhandled() -> dict[str, str]:
        raise RuntimeError("secret internal detail")

    @test_app.get("/typed/{item_id}")
    async def typed(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("error_name", "status_code", "error_code"),
    [
        ("not_found", 404, "not_found"),
        ("validation", 400, "validation_error"),
        ("authentication", 401, "authentication_error"),
        ("authorization", 403, "authorization_error"),
        ("conflict", 409, "conflict"),
        ("external", 503, "external_service_error"),
    ],
)
def test_api_errors_map_to_status_codes(
    client: TestClient, error_name: str, status_code: int, error_code: str
) -> None:
    """Test that each error class produces its HTTP status and envelope."""
    response = client.get(f"/boom/{error_name}")
    assert response.status_code == status_code

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == error_code
    assert body["error"]["message"]
    assert body["request_id"]
    assert body["timestamp"]


def test_unhandled_exception_returns_500_envelope(client: TestClient) -> None:
    """Test that unexpected exceptions produce a standard 500 envelope."""
    response = client.get("/unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "internal_error"


def test_unhandled_exception_message_visible_in_development(client: TestClient) -> None:
    """Test that development environments surface the real error message."""
    response = client.get("/unhandled")
    assert "secret internal detail" in response.json()["error"]["message"]


def test_unhandled_exception_sanitized_in_production(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that production responses never leak internal error details."""
    import src.middleware.error_handler as handler_module

    monkeypatch.setattr(
        handler_module, "get_settings", lambda: SimpleNamespace(environment="production")
    )
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/unhandled")
    assert response.status_code == 500
    message = response.json()["error"]["message"]
    assert "secret internal detail" not in message


def test_unhandled_exception_is_logged_with_request_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that server errors are logged with traceback context."""
    with caplog.at_level(logging.ERROR, logger="ai_ea.errors"):
        client.get("/unhandled")
    assert any("secret internal detail" in r.getMessage() or r.exc_info for r in caplog.records)


def test_request_validation_error_uses_envelope(client: TestClient) -> None:
    """Test that FastAPI validation failures use the standard envelope."""
    response = client.get("/typed/not-an-int")
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"], "Validation errors should include field details"


def test_unknown_route_returns_envelope_on_main_app() -> None:
    """Test that the real application envelopes plain HTTP errors (404)."""
    from src.main import app as main_app

    client = TestClient(main_app)
    response = client.get("/definitely-not-a-route")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "http_error"


def test_health_endpoint_contract_unchanged() -> None:
    """Test that /health still returns the exact original payload."""
    from src.main import app as main_app

    client = TestClient(main_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_detailed_health_reports_component_checks() -> None:
    """Test that /health/detailed reports per-dependency status."""
    from src.main import app as main_app

    client = TestClient(main_app)
    response = client.get("/health/detailed")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("healthy", "degraded")

    checks = body["checks"]
    assert checks["database"]["status"] in ("up", "down")
    assert "redis" in checks
    assert "external_services" in checks


def test_success_response_factory() -> None:
    """Test the success envelope factory."""
    envelope = success_response({"a": 1}, request_id="req-123")
    assert envelope.success is True
    assert envelope.data == {"a": 1}
    assert envelope.error is None
    assert envelope.request_id == "req-123"
    assert envelope.timestamp is not None


def test_error_detail_and_pagination_models() -> None:
    """Test the supporting response models validate as expected."""
    detail = ErrorDetail(code="conflict", message="Already exists")
    assert detail.details is None

    page = PaginatedData(items=[1, 2, 3], total=10, limit=3, offset=0)
    assert page.total == 10
    assert len(page.items) == 3
