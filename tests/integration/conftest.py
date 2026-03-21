"""Integration test fixtures: MongoDB testcontainer + FastAPI test client."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer

from src.application.services.location_service_impl import LocationServiceImpl
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from src.infrastructure.adapters.outbound.persistence.mongo_location_repository import MongoLocationRepository
from tests.conftest import ALL_PERMISSIONS, auth_header, override_auth

_MONGO_IMAGE = "mongo:7"


@pytest.fixture(scope="session")
def mongo_container():
    """Start a MongoDB testcontainer for the entire test session."""
    with MongoDbContainer(image=_MONGO_IMAGE) as container:
        yield container


@pytest.fixture()
async def mongo_collection(mongo_container):
    """Provide a clean MongoDB collection for each test, dropping it afterwards."""
    client = AsyncIOMotorClient(mongo_container.get_connection_url())
    db = client["hhh_maps_test"]
    collection = db["locations"]
    await collection.drop()
    yield collection
    await collection.drop()
    client.close()


@pytest.fixture()
async def api_client(mongo_collection) -> AsyncGenerator[AsyncClient, None]:
    """Return an httpx.AsyncClient wired to a real MongoDB collection."""
    from fastapi import FastAPI

    repository = MongoLocationRepository(mongo_collection)
    service = LocationServiceImpl(repository)
    init_router(service)

    app = FastAPI()
    app.include_router(router)
    override_auth(app, ALL_PERMISSIONS)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture()
def read_headers() -> dict[str, str]:
    return auth_header(["hhh:locations:read"])


@pytest.fixture()
def all_headers() -> dict[str, str]:
    return auth_header(ALL_PERMISSIONS)
