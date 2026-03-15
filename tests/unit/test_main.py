"""Unit tests for CORS middleware configuration in create_app."""

from unittest.mock import MagicMock, patch

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


def _create_test_app() -> TestClient:
    """Create a test client from the real app with mocked external dependencies."""
    with (
        patch("src.main.Settings") as mock_settings_cls,
        patch("src.main.Injector") as mock_injector_cls,
        patch("src.main.init_router"),
    ):
        mock_settings = MagicMock()
        mock_settings.app_name = "test-maps"
        mock_settings_cls.return_value = mock_settings
        mock_injector_cls.return_value = MagicMock()

        from src.main import create_app

        app = create_app()

    cors_middleware = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    assert len(cors_middleware) == 1
    return TestClient(app)


@patch("src.infrastructure.config.dependencies.MongoClient")
class TestCORSMiddleware:
    """Tests for CORS middleware on the FastAPI app."""

    def test_cors_allows_localhost_3000(self, _mock_mongo: MagicMock) -> None:
        client = _create_test_app()
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_allows_localhost_3001(self, _mock_mongo: MagicMock) -> None:
        client = _create_test_app()
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers["access-control-allow-origin"] == "http://localhost:3001"

    def test_cors_rejects_disallowed_origin(self, _mock_mongo: MagicMock) -> None:
        client = _create_test_app()
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:9999",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    def test_cors_header_on_regular_get(self, _mock_mongo: MagicMock) -> None:
        client = _create_test_app()
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
