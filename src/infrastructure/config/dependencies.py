from hexadian_auth_common.fastapi import JWTAuthDependency
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from opyoid import Module, SingletonScope
from pymongo.collation import Collation

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.application.ports.inbound.location_service import LocationService
from src.application.ports.outbound.location_distance_repository import LocationDistanceRepository
from src.application.ports.outbound.location_repository import LocationRepository
from src.application.services.location_distance_service_impl import LocationDistanceServiceImpl
from src.application.services.location_service_impl import LocationServiceImpl
from src.infrastructure.adapters.outbound.persistence.mongo_location_distance_repository import (
    MongoLocationDistanceRepository,
)
from src.infrastructure.adapters.outbound.persistence.mongo_location_repository import MongoLocationRepository
from src.infrastructure.config.settings import Settings


class AppModule(Module):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._client = AsyncIOMotorClient(settings.mongo_uri)
        db = self._client[settings.mongo_db]
        self._location_collection: AsyncIOMotorCollection = db["locations"]
        self._distance_collection: AsyncIOMotorCollection = db["location_distances"]

    def configure(self) -> None:
        self.bind(AsyncIOMotorCollection, to_instance=self._location_collection, scope=SingletonScope)
        self.bind(LocationRepository, to_class=MongoLocationRepository, scope=SingletonScope)
        self.bind(LocationService, to_class=LocationServiceImpl, scope=SingletonScope)

        distance_repo = MongoLocationDistanceRepository(self._distance_collection)
        self.bind(LocationDistanceRepository, to_instance=distance_repo, scope=SingletonScope)
        self.bind(LocationDistanceService, to_class=LocationDistanceServiceImpl, scope=SingletonScope)

        jwt_auth = JWTAuthDependency(
            secret=self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )
        self.bind(JWTAuthDependency, to_instance=jwt_auth, scope=SingletonScope)

    def close(self) -> None:
        """Close the motor client and release connection pool resources."""
        self._client.close()

    async def create_indexes(self) -> None:
        await self._location_collection.create_index("location_type")
        await self._location_collection.create_index("parent_id")
        await self._location_collection.create_index("name", collation=Collation(locale="en", strength=2))

        info = await self._distance_collection.index_information()
        if "from_location_id_1_to_location_id_1" in info:
            await self._distance_collection.drop_index("from_location_id_1_to_location_id_1")
        await self._distance_collection.create_index(
            [("from_location_id", 1), ("to_location_id", 1), ("travel_type", 1)],
            unique=True,
        )
        await self._distance_collection.create_index("from_location_id")
        await self._distance_collection.create_index("to_location_id")
