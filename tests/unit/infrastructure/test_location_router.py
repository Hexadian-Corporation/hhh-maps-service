"""Unit tests for the search endpoint in location_router."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_router import init_router, router


def _make_client(service: MagicMock) -> TestClient:
    init_router(service)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _make_location(location_id: str = "abc123", name: str = "Lorville") -> Location:
    return Location(
        id=location_id,
        name=name,
        location_type="city",
        parent_id="parent1",
        coordinates=Coordinates(x=1.0, y=2.0, z=3.0),
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


class TestSearchEndpoint:
    """Verify GET /locations/search?q= endpoint behavior."""

    def test_search_returns_matching_locations(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/search?q=lor")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Lorville"
        service.search_by_name.assert_called_once_with("lor")

    def test_search_empty_query_returns_empty_list(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = []
        client = _make_client(service)

        response = client.get("/locations/search?q=")

        assert response.status_code == 200
        assert response.json() == []

    def test_search_no_query_param_returns_empty_list(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = []
        client = _make_client(service)

        response = client.get("/locations/search")

        assert response.status_code == 200
        assert response.json() == []

    def test_search_multiple_results(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = [
            _make_location("id1", "Port Olisar"),
            _make_location("id2", "Port Tressler"),
        ]
        client = _make_client(service)

        response = client.get("/locations/search?q=port")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Port Olisar"
        assert data[1]["name"] == "Port Tressler"

    def test_search_returns_correct_dto_fields(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/search?q=lor")

        data = response.json()[0]
        assert data["_id"] == "abc123"
        assert data["name"] == "Lorville"
        assert data["location_type"] == "city"
        assert data["parent_id"] == "parent1"
        assert data["coordinates"] == {"x": 1.0, "y": 2.0, "z": 3.0}
        assert data["has_trade_terminal"] is True
        assert data["has_landing_pad"] is True
        assert data["landing_pad_size"] == "large"


class TestGetLocationEndpoint:
    """Verify GET /locations/{location_id} returns 404 when not found."""

    def test_get_returns_404_for_nonexistent(self) -> None:
        service = MagicMock()
        service.get.side_effect = LocationNotFoundError("missing-id")
        client = _make_client(service)

        response = client.get("/locations/missing-id")

        assert response.status_code == 404


class TestDeleteLocationEndpoint:
    """Verify DELETE /locations/{location_id} returns 404 when not found."""

    def test_delete_returns_404_for_nonexistent(self) -> None:
        service = MagicMock()
        service.delete.side_effect = LocationNotFoundError("missing-id")
        client = _make_client(service)

        response = client.delete("/locations/missing-id")

        assert response.status_code == 404
