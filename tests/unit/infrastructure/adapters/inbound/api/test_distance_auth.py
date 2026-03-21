"""Unit tests for JWT authentication on distance endpoints."""

from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexadian_auth_common.fastapi import JWTAuthDependency, _stub_jwt_auth, register_exception_handlers

from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.inbound.api.location_distance_router import distance_router, init_distance_router
from tests.conftest import JWT_ALGORITHM, JWT_SECRET, auth_header


def _make_auth_client(service: AsyncMock | None = None) -> TestClient:
    """Create a test client with real JWT auth configured."""
    if service is None:
        service = AsyncMock()
    init_distance_router(service)

    app = FastAPI()
    jwt_auth = JWTAuthDependency(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
    register_exception_handlers(app)
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth
    app.include_router(distance_router)
    return TestClient(app)


def _make_distance(distance_id: str = "abc123") -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id="loc-a",
        to_location_id="loc-b",
        distance=1500.0,
        travel_type="quantum",
    )


class TestAuthenticationRequired:
    """Verify that endpoints return 401 when no token is provided."""

    def test_create_distance_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.post(
            "/distances/",
            json={"from_location_id": "loc-a", "to_location_id": "loc-b", "distance": 1.0, "travel_type": "scm"},
        )
        assert response.status_code == 401

    def test_get_distance_by_pair_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b")
        assert response.status_code == 401

    def test_update_distance_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.put("/distances/abc123", json={"distance": 100.0})
        assert response.status_code == 401

    def test_delete_distance_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.delete("/distances/abc123")
        assert response.status_code == 401

    def test_get_distances_from_location_requires_auth(self) -> None:
        client = _make_auth_client()
        response = client.get("/locations/loc-a/distances")
        assert response.status_code == 401


class TestInvalidToken:
    """Verify that endpoints return 401 for invalid JWT tokens."""

    def test_invalid_token_returns_401(self) -> None:
        client = _make_auth_client()
        response = client.get(
            "/distances/?from_location_id=loc-a&to_location_id=loc-b",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"], exp=0)
        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b", headers=headers)
        assert response.status_code == 401


class TestInsufficientPermissions:
    """Verify that endpoints return 403 when the user lacks the required permission."""

    def test_create_requires_write_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.post(
            "/distances/",
            json={"from_location_id": "loc-a", "to_location_id": "loc-b", "distance": 1.0, "travel_type": "scm"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_get_distance_by_pair_requires_read_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:write"])
        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b", headers=headers)
        assert response.status_code == 403

    def test_update_requires_write_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.put("/distances/abc123", json={"distance": 100.0}, headers=headers)
        assert response.status_code == 403

    def test_delete_requires_delete_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:read"])
        response = client.delete("/distances/abc123", headers=headers)
        assert response.status_code == 403

    def test_get_distances_from_location_requires_read_permission(self) -> None:
        client = _make_auth_client()
        headers = auth_header(["hhh:locations:write"])
        response = client.get("/locations/loc-a/distances", headers=headers)
        assert response.status_code == 403


class TestValidPermissions:
    """Verify that endpoints succeed with the correct permissions."""

    def test_create_with_write_permission(self) -> None:
        service = AsyncMock()
        service.create.return_value = _make_distance()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:write"])

        response = client.post(
            "/distances/",
            json={"from_location_id": "loc-a", "to_location_id": "loc-b", "distance": 1500.0, "travel_type": "quantum"},
            headers=headers,
        )
        assert response.status_code == 201

    def test_get_distance_by_pair_with_read_permission(self) -> None:
        service = AsyncMock()
        service.get_by_pair.return_value = _make_distance()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:read"])

        response = client.get("/distances/?from_location_id=loc-a&to_location_id=loc-b", headers=headers)
        assert response.status_code == 200

    def test_update_with_write_permission(self) -> None:
        service = AsyncMock()
        service.get.return_value = _make_distance()
        service.update.return_value = _make_distance()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:write"])

        response = client.put("/distances/abc123", json={"distance": 999.0}, headers=headers)
        assert response.status_code == 200

    def test_delete_with_delete_permission(self) -> None:
        service = AsyncMock()
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:delete"])

        response = client.delete("/distances/abc123", headers=headers)
        assert response.status_code == 204

    def test_get_distances_from_location_with_read_permission(self) -> None:
        service = AsyncMock()
        service.get_by_location.return_value = [_make_distance()]
        client = _make_auth_client(service)
        headers = auth_header(["hhh:locations:read"])

        response = client.get("/locations/loc-a/distances", headers=headers)
        assert response.status_code == 200
