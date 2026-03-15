"""Unit tests for src.main – app creation and lifespan seeding."""

from unittest.mock import MagicMock, patch

# Patch MongoClient before importing src.main to prevent the module-level
# ``app = create_app()`` from connecting to MongoDB during test collection.
with patch("src.infrastructure.config.dependencies.MongoClient", return_value=MagicMock()):
    from src.main import create_app

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
        mock_injector = MagicMock()
        mock_injector.inject.return_value = mock_service
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
        mock_injector.inject.return_value = MagicMock()
        mock_injector_cls.return_value = mock_injector

        app = create_app()
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok", "service": "test-maps"}
