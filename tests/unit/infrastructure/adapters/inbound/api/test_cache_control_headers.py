"""Unit tests for Cache-Control headers on list and search endpoints."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from tests.conftest import override_auth


def _make_client(service: MagicMock) -> TestClient:
    init_router(service)
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
        coordinates=Coordinates(x=1.0, y=2.0, z=3.0),
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


class TestCacheControlHeaders:
    """Verify Cache-Control header is present on GET /locations/ and GET /locations/search."""

    def test_list_all_has_cache_control(self) -> None:
        service = MagicMock()
        service.list_all.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_list_by_type_has_cache_control(self) -> None:
        service = MagicMock()
        service.list_by_type.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/?location_type=station")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_list_by_parent_has_cache_control(self) -> None:
        service = MagicMock()
        service.list_children.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/?parent_id=sys-1")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_search_has_cache_control(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = [_make_location()]
        client = _make_client(service)

        response = client.get("/locations/search?q=port")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"

    def test_search_empty_has_cache_control(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = []
        client = _make_client(service)

        response = client.get("/locations/search?q=")

        assert response.status_code == 200
        assert response.headers.get("cache-control") == "max-age=300"
