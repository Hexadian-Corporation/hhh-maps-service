"""Unit tests for Cache-Control headers on distance GET endpoints."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.inbound.api.location_distance_router import distance_router, init_distance_router
from tests.conftest import override_auth


def _make_client(service: MagicMock) -> TestClient:
    init_distance_router(service)
    app = FastAPI()
    app.include_router(distance_router)
    override_auth(app)
    return TestClient(app)


def _make_distance(distance_id: str = "abc123") -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id="loc-a",
        to_location_id="loc-b",
        distance=1500.0,
        travel_type="quantum",
    )


class TestDistanceCacheControlHeaders:
    """Verify Cache-Control header is present on distance GET endpoints."""

    def test_get_by_pair_has_cache_control(self) -> None:
        service = MagicMock()
        service.get_by_pair.return_value = _make_distance()
        client = _make_client(service)

        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_get_distances_from_location_has_cache_control(self) -> None:
        service = MagicMock()
        service.get_by_location.return_value = [_make_distance()]
        client = _make_client(service)

        response = client.get("/locations/loc-a/distances")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_get_distances_from_location_empty_has_cache_control(self) -> None:
        service = MagicMock()
        service.get_by_location.return_value = []
        client = _make_client(service)

        response = client.get("/locations/loc-z/distances")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"
