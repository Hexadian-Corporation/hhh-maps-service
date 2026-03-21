"""Unit tests for location router endpoints."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Location
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from tests.conftest import override_auth


def _make_app() -> TestClient:
    """Create a test client with a fresh FastAPI app including the locations router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    override_auth(app)
    return TestClient(app)


def _make_location(location_id: str = "abc123") -> Location:
    return Location(
        id=location_id,
        name="Port Olisar",
        location_type="station",
        parent_id="sys-1",
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


class TestGetLocationEndpoint:
    """Tests for GET /locations/{location_id} 404 path."""

    def test_get_returns_404_for_nonexistent(self) -> None:
        service = AsyncMock()
        service.get.side_effect = LocationNotFoundError("missing-id")
        init_router(service)

        client = _make_app()
        response = client.get("/locations/missing-id")

        assert response.status_code == 404


class TestDeleteLocationEndpoint:
    """Tests for DELETE /locations/{location_id} 404 path."""

    def test_delete_returns_404_for_nonexistent(self) -> None:
        service = AsyncMock()
        service.delete.side_effect = LocationNotFoundError("missing-id")
        init_router(service)

        client = _make_app()
        response = client.delete("/locations/missing-id")

        assert response.status_code == 404


class TestUpdateLocationEndpoint:
    """Tests for PUT /locations/{location_id}."""

    def test_update_returns_200_with_updated_location(self) -> None:
        service = AsyncMock()
        existing = _make_location()
        updated = _make_location()
        updated.name = "Updated Name"
        service.get.return_value = existing
        service.update.return_value = updated
        init_router(service)

        client = _make_app()
        response = client.put("/locations/abc123", json={"name": "Updated Name"})

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["location_type"] == "station"

    def test_update_partial_fields(self) -> None:
        service = AsyncMock()
        existing = _make_location()
        updated = _make_location()
        updated.has_trade_terminal = False
        service.get.return_value = existing
        service.update.return_value = updated
        init_router(service)

        client = _make_app()
        response = client.put("/locations/abc123", json={"has_trade_terminal": False})

        assert response.status_code == 200
        data = response.json()
        assert data["has_trade_terminal"] is False

    def test_update_returns_404_for_nonexistent(self) -> None:
        service = AsyncMock()
        service.get.side_effect = LocationNotFoundError("missing-id")
        init_router(service)

        client = _make_app()
        response = client.put("/locations/missing-id", json={"name": "X"})

        assert response.status_code == 404

    def test_update_empty_body_preserves_existing(self) -> None:
        service = AsyncMock()
        existing = _make_location()
        service.get.return_value = existing
        service.update.return_value = existing
        init_router(service)

        client = _make_app()
        response = client.put("/locations/abc123", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Port Olisar"


class TestGetAncestorsEndpoint:
    """Tests for GET /locations/{location_id}/ancestors."""

    def test_returns_200_with_ancestor_list(self) -> None:
        service = AsyncMock()
        city = _make_location("city-1")
        city.location_type = "city"
        planet = _make_location("planet-1")
        planet.location_type = "planet"
        planet.parent_id = None
        service.get_ancestors.return_value = [city, planet]
        init_router(service)

        client = _make_app()
        response = client.get("/locations/city-1/ancestors")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["_id"] == "city-1"
        assert data[1]["_id"] == "planet-1"

    def test_returns_404_for_nonexistent_location(self) -> None:
        service = AsyncMock()
        service.get_ancestors.side_effect = LocationNotFoundError("missing-id")
        init_router(service)

        client = _make_app()
        response = client.get("/locations/missing-id/ancestors")

        assert response.status_code == 404

    def test_returns_cache_control_header(self) -> None:
        service = AsyncMock()
        service.get_ancestors.return_value = [_make_location("loc-1")]
        init_router(service)

        client = _make_app()
        response = client.get("/locations/loc-1/ancestors")

        assert response.status_code == 200
        assert response.headers["cache-control"] == "max-age=300"
