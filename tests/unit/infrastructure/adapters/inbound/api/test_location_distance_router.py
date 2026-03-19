"""Unit tests for location distance router endpoints."""

from unittest.mock import MagicMock

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
        service = MagicMock()
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


class TestGetDistanceByPairEndpoint:
    def test_get_by_pair_returns_200(self) -> None:
        service = MagicMock()
        service.get_by_pair.return_value = _make_distance()
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b")

        assert response.status_code == 200
        data = response.json()
        assert data["from_location_id"] == "loc-a"
        assert response.headers.get("cache-control") == "max-age=300"

    def test_get_by_pair_returns_404_when_not_found(self) -> None:
        service = MagicMock()
        service.get_by_pair.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.get("/distances/?from_location_id=loc-x&to_location_id=loc-y")

        assert response.status_code == 404


class TestUpdateDistanceEndpoint:
    def test_update_returns_200(self) -> None:
        service = MagicMock()
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
        service = MagicMock()
        service.get.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.put("/distances/missing", json={"distance": 100.0})

        assert response.status_code == 404


class TestDeleteDistanceEndpoint:
    def test_delete_returns_204(self) -> None:
        service = MagicMock()
        init_distance_router(service)

        client = _make_app()
        response = client.delete("/distances/d-1")

        assert response.status_code == 204

    def test_delete_returns_404_for_nonexistent(self) -> None:
        service = MagicMock()
        service.delete.side_effect = LocationDistanceNotFoundError("missing")
        init_distance_router(service)

        client = _make_app()
        response = client.delete("/distances/missing")

        assert response.status_code == 404


class TestGetDistancesFromLocationEndpoint:
    def test_returns_list_with_cache_header(self) -> None:
        service = MagicMock()
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
        service = MagicMock()
        service.get_by_location.return_value = []
        init_distance_router(service)

        client = _make_app()
        response = client.get("/locations/loc-z/distances")

        assert response.status_code == 200
        assert response.json() == []
