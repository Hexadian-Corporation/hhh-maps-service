"""Unit tests for src.main – app creation, lifespan seeding, and CORS middleware."""

from unittest.mock import MagicMock, patch

# Patch MongoClient before importing src.main to prevent the module-level
# ``app = create_app()`` from connecting to MongoDB during test collection.
with patch("src.infrastructure.config.dependencies.MongoClient", return_value=MagicMock()):
    from src.main import create_app

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


class TestLifespanSeedsLocations:
    """Verify that create_app produces an app whose lifespan calls seed_locations."""

    @patch("src.main.seed_locations")
    @patch("src.main.Injector")
    @patch("src.main.Settings")
    def test_seed_locations_called_on_startup(
        self,
        mock_settings_cls: MagicMock,
        mock_injector_cls: MagicMock,
        mock_seed: MagicMock,
    ) -> None:
        mock_settings = MagicMock()
        mock_settings.app_name = "test-app"
        mock_settings_cls.return_value = mock_settings

        mock_service = MagicMock()
        mock_distance_service = MagicMock()
        mock_jwt_auth = MagicMock()
        mock_injector = MagicMock()
        mock_injector.inject.side_effect = [mock_service, mock_distance_service, mock_jwt_auth]
        mock_injector_cls.return_value = mock_injector

        app = create_app()

        # seed_locations is called during lifespan startup, not during create_app
        mock_seed.assert_not_called()

        # Trigger lifespan by using TestClient as context manager
        with TestClient(app):
            mock_seed.assert_called_once_with(mock_service)

    @patch("src.main.seed_locations")
    @patch("src.main.Injector")
    @patch("src.main.Settings")
    def test_health_endpoint_still_works(
        self,
        mock_settings_cls: MagicMock,
        mock_injector_cls: MagicMock,
        mock_seed: MagicMock,
    ) -> None:
        mock_settings = MagicMock()
        mock_settings.app_name = "test-maps"
        mock_settings_cls.return_value = mock_settings

        mock_injector = MagicMock()
        mock_injector.inject.side_effect = [MagicMock(), MagicMock(), MagicMock()]
        mock_injector_cls.return_value = mock_injector

        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok", "service": "test-maps"}


def _create_test_app() -> TestClient:
    """Create a test client from the real app with mocked external dependencies."""
    with (
        patch("src.main.Settings") as mock_settings_cls,
        patch("src.main.Injector") as mock_injector_cls,
        patch("src.main.init_router"),
        patch("src.main.init_distance_router"),
        patch("src.main.seed_locations"),
    ):
        mock_settings = MagicMock()
        mock_settings.app_name = "test-maps"
        mock_settings_cls.return_value = mock_settings
        mock_injector_cls.return_value = MagicMock()

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
