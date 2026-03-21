"""Unit tests for location distance router endpoints."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.domain.exceptions.location_distance_exceptions import LocationDistanceNotFoundError
from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.inbound.api.location_distance_router import distance_router, init_distance_router
from tests.conftest import override_auth


def _make_app() -> TestClient:
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(distance_router)
    override_auth(app)
    return TestClient(app)


def _make_distance(distance_id: str = "d-1") -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id="loc-a",
        to_location_id="loc-b",
        distance=1500.0,
        travel_type="quantum",
    )


class TestCreateDistanceEndpoint:
    def test_create_returns_201(self) -> None:
        service = AsyncMock()
        service.create.return_value = _make_distance()
        init_distance_router(service)

        client = _make_app()
        response = client.post(
            "/distances/",
            json={"from_location_id": "loc-a", "to_location_id": "loc-b", "distance": 1500.0, "travel_type": "quantum"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["from_location_id"] == "loc-a"
        assert data["to_location_id"] == "loc-b"
        assert data["distance"] == 1500.0
        assert data["travel_type"] == "quantum"


class TestListDistancesEndpoint:
    def test_get_by_pair_returns_list_with_match(self) -> None:
        service = AsyncMock()
        service.get_by_pair.return_value = _make_distance()
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["from_location_id"] == "loc-a"
        assert response.headers.get("cache-control") == "max-age=300"

    def test_get_by_pair_returns_empty_list_when_not_found(self) -> None:
        service = AsyncMock()
        service.get_by_pair.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?from_location_id=loc-x&to_location_id=loc-y")

        assert response.status_code == 200
        assert response.json() == []

    def test_filter_by_travel_type_returns_matching_list(self) -> None:
        service = AsyncMock()
        service.list_by_travel_type.return_value = [_make_distance()]
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?travel_type=wormhole")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        service.list_by_travel_type.assert_called_once_with("wormhole")
        assert response.headers.get("cache-control") == "max-age=300"

    def test_no_params_returns_all_distances(self) -> None:
        service = AsyncMock()
        service.list_all.return_value = [_make_distance("d-1"), _make_distance("d-2")]
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        service.list_all.assert_called_once()
        assert response.headers.get("cache-control") == "max-age=300"

    def test_filter_by_travel_type_returns_empty_list(self) -> None:
        service = AsyncMock()
        service.list_by_travel_type.return_value = []
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?travel_type=on_foot")

        assert response.status_code == 200
        assert response.json() == []


class TestUpdateDistanceEndpoint:
    def test_update_returns_200(self) -> None:
        service = AsyncMock()
        existing = _make_distance()
        updated = LocationDistance(
            id="d-1",
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=999.0,
            travel_type="quantum",
        )
        service.get.return_value = existing
        service.update.return_value = updated
        init_distance_router(service)

        client = _make_app()
        response = client.put("/distances/d-1", json={"distance": 999.0})

        assert response.status_code == 200
        data = response.json()
        assert data["distance"] == 999.0

    def test_update_returns_404_for_nonexistent(self) -> None:
        service = AsyncMock()
        service.get.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.put("/distances/missing", json={"distance": 100.0})

        assert response.status_code == 404


class TestDeleteDistanceEndpoint:
    def test_delete_returns_204(self) -> None:
        service = AsyncMock()
        init_distance_router(service)

        client = _make_app()
        response = client.delete("/distances/d-1")

        assert response.status_code == 204

    def test_delete_returns_404_for_nonexistent(self) -> None:
        service = AsyncMock()
        service.delete.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.delete("/distances/missing")

        assert response.status_code == 404


class TestGetDistancesFromLocationEndpoint:
    def test_returns_list_with_cache_header(self) -> None:
        service = AsyncMock()
        service.get_by_location.return_value = [_make_distance()]
        init_distance_router(service)

        client = _make_app()
        response = client.get("/locations/loc-a/distances")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["from_location_id"] == "loc-a"
        assert response.headers.get("cache-control") == "max-age=300"

    def test_returns_empty_list(self) -> None:
        service = AsyncMock()
        service.get_by_location.return_value = []
        init_distance_router(service)

        client = _make_app()
        response = client.get("/locations/loc-z/distances")

        assert response.status_code == 200
        assert response.json() == []
