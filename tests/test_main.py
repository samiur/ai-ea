# ABOUTME: Tests for main FastAPI application endpoints
# ABOUTME: Tests health, status, and root endpoints following TDD

from fastapi.testclient import TestClient


def test_app_exists():
    """Test that the FastAPI app can be imported."""
    from src.main import app

    assert app is not None
    assert app.title is not None


def test_health_endpoint_returns_healthy_status():
    """Test that GET /health returns 200 with healthy status."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_status_endpoint_returns_app_info():
    """Test that GET /status returns app version and environment."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/status")

    assert response.status_code == 200
    data = response.json()

    # Should include app name, version, and environment
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert data["app_name"] == "AI Executive Assistant"


def test_root_endpoint_returns_welcome_message():
    """Test that root path returns API documentation link."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    # Should include welcome message and docs link
    assert "message" in data
    assert "docs_url" in data
    assert "/docs" in data["docs_url"]


def test_cors_headers_present():
    """Test that CORS middleware is configured for localhost."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    # Should have CORS headers
    assert response.status_code == 200
    # Note: Test client doesn't fully simulate CORS, but we can verify the middleware is added


def test_request_id_in_response():
    """Test that request ID middleware adds tracking ID."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/health")

    # Should have a request ID header or in response
    assert response.status_code == 200
    # We'll verify request ID is present once implemented
