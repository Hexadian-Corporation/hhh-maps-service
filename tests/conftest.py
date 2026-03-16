"""Shared test fixtures and helpers for JWT authentication."""

import jwt
import pytest
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

JWT_SECRET = "test-secret-key-with-sufficient-length"
JWT_ALGORITHM = "HS256"

ALL_PERMISSIONS = ["locations:read", "locations:write", "locations:delete"]


def make_token(permissions: list[str] | None = None, **extra_claims: object) -> str:
    """Create a valid JWT token with the given permissions."""
    claims: dict = {
        "sub": "user-1",
        "username": "testuser",
        "permissions": permissions or [],
        **extra_claims,
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


def auth_header(permissions: list[str] | None = None, **extra_claims: object) -> dict[str, str]:
    """Return an Authorization header dict with a valid Bearer token."""
    token = make_token(permissions, **extra_claims)
    return {"Authorization": f"Bearer {token}"}


def override_auth(app: object, permissions: list[str] | None = None) -> None:
    """Override _stub_jwt_auth in a FastAPI app to bypass real JWT validation.

    Useful for unit tests that test router logic rather than auth logic.
    """
    user = UserContext(
        user_id="test-user",
        username="testuser",
        permissions=permissions or ALL_PERMISSIONS,
    )

    async def _fake_auth() -> UserContext:
        return user

    app.dependency_overrides[_stub_jwt_auth] = _fake_auth  # type: ignore[attr-defined]


@pytest.fixture()
def read_headers() -> dict[str, str]:
    """Auth headers with locations:read permission."""
    return auth_header(["locations:read"])


@pytest.fixture()
def write_headers() -> dict[str, str]:
    """Auth headers with locations:write permission."""
    return auth_header(["locations:write"])


@pytest.fixture()
def delete_headers() -> dict[str, str]:
    """Auth headers with locations:delete permission."""
    return auth_header(["locations:delete"])


@pytest.fixture()
def all_headers() -> dict[str, str]:
    """Auth headers with all location permissions."""
    return auth_header(ALL_PERMISSIONS)
