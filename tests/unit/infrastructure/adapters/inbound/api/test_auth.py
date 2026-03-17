"""Unit tests for JWT authentication on location endpoints."""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexadian_auth_common.fastapi import JWTAuthDependency, _stub_jwt_auth, register_exception_handlers

from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from tests.conftest import JWT_ALGORITHM, JWT_SECRET, auth_header


def _make_auth_client(service: MagicMock | None = None) -> TestClient:
    """Create a test client with real JWT auth configured."""
    if service is None:
        service = MagicMock()
    init_router(service)

    app = FastAPI()
    jwt_auth = JWTAuthDependency(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
    register_exception_handlers(app)
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth
    app.include_router(router)
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


class TestAuthenticationRequired:
    """Verify that endpoints return 401 when no token is provided."""

    def test_get_locations_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.get("/locations/")
        assert response.status_code == 401

    def test_get_location_by_id_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.get("/locations/abc123")
        assert response.status_code == 401

    def test_search_locations_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.get("/locations/search?q=port")
        assert response.status_code == 401

    def test_create_location_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.post("/locations/", json={"name": "Test", "location_type": "station"})
        assert response.status_code == 401

    def test_update_location_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.put("/locations/abc123", json={"name": "Updated"})
        assert response.status_code == 401

    def test_delete_location_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.delete("/locations/abc123")
        assert response.status_code == 401


class TestInvalidToken:
    """Verify that endpoints return 401 for invalid JWT tokens."""

    def test_invalid_token_returns_401(self) -> None:
        client = _make_auth_client()
        response = client.get("/locations/", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401

    def test_expired_token_returns_401(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"], exp=0)
        response = client.get("/locations/", headers=headers)
        assert response.status_code == 401


class TestInsufficientPermissions:
    """Verify that endpoints return 403 when the user lacks the required permission."""

    def test_create_requires_write_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.post("/locations/", json={"name": "Test", "location_type": "station"}, headers=headers)
        assert response.status_code == 403

    def test_get_locations_requires_read_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:write"])
        response = client.get("/locations/", headers=headers)
        assert response.status_code == 403

    def test_get_location_by_id_requires_read_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:write"])
        response = client.get("/locations/abc123", headers=headers)
        assert response.status_code == 403

    def test_search_requires_read_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:write"])
        response = client.get("/locations/search?q=port", headers=headers)
        assert response.status_code == 403

    def test_update_requires_write_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.put("/locations/abc123", json={"name": "Updated"}, headers=headers)
        assert response.status_code == 403

    def test_delete_requires_delete_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.delete("/locations/abc123", headers=headers)
        assert response.status_code == 403


class TestValidPermissions:
    """Verify that endpoints succeed with the correct permissions."""

    def test_get_locations_with_read_permission(self) -> None:
        service = MagicMock()
        service.list_all.return_value = [_make_location()]
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:read"])

        response = client.get("/locations/", headers=headers)
        assert response.status_code == 200

    def test_get_location_by_id_with_read_permission(self) -> None:
        service = MagicMock()
        service.get.return_value = _make_location()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:read"])

        response = client.get("/locations/abc123", headers=headers)
        assert response.status_code == 200

    def test_search_with_read_permission(self) -> None:
        service = MagicMock()
        service.search_by_name.return_value = [_make_location()]
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:read"])

        response = client.get("/locations/search?q=port", headers=headers)
        assert response.status_code == 200

    def test_create_with_write_permission(self) -> None:
        service = MagicMock()
        service.create.return_value = _make_location()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:write"])

        response = client.post(
            "/locations/",
            json={"name": "Port Olisar", "location_type": "station"},
            headers=headers,
        )
        assert response.status_code == 201

    def test_update_with_write_permission(self) -> None:
        service = MagicMock()
        service.get.return_value = _make_location()
        service.update.return_value = _make_location()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:write"])

        response = client.put("/locations/abc123", json={"name": "Updated"}, headers=headers)
        assert response.status_code == 200

    def test_delete_with_delete_permission(self) -> None:
        service = MagicMock()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:delete"])

        response = client.delete("/locations/abc123", headers=headers)
        assert response.status_code == 204
