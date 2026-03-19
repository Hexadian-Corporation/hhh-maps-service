from hexadian_auth_common.fastapi import JWTAuthDependency
from opyoid import Module, SingletonScope
from pymongo import MongoClient
from pymongo.collation import Collation
from pymongo.collection import Collection

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

    def configure(self) -> None:
        client = MongoClient(self._settings.mongo_uri)
        db = client[self._settings.mongo_db]
        collection = db["locations"]
        distance_collection = db["location_distances"]

        collection.create_index("location_type")
        collection.create_index("parent_id")
        collection.create_index("name", collation=Collation(locale="en", strength=2))

        distance_collection.create_index(
            [("from_location_id", 1), ("to_location_id", 1)],
            unique=True,
        )
        distance_collection.create_index("to_location_id")

        self.bind(Collection, to_instance=collection, scope=SingletonScope)
        self.bind(LocationRepository, to_class=MongoLocationRepository, scope=SingletonScope)
        self.bind(LocationService, to_class=LocationServiceImpl, scope=SingletonScope)

        distance_repo = MongoLocationDistanceRepository(distance_collection)
        self.bind(LocationDistanceRepository, to_instance=distance_repo, scope=SingletonScope)
        self.bind(LocationDistanceService, to_class=LocationDistanceServiceImpl, scope=SingletonScope)

        jwt_auth = JWTAuthDependency(
            secret=self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )
        self.bind(JWTAuthDependency, to_instance=jwt_auth, scope=SingletonScope)
