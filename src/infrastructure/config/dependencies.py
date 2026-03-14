from opyoid import Module, SingletonScope
from pymongo import MongoClient
from pymongo.collection import Collection

from src.application.ports.inbound.location_service import LocationService
from src.application.ports.outbound.location_repository import LocationRepository
from src.application.services.location_service_impl import LocationServiceImpl
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

        self.bind(Collection, to_instance=collection, scope=SingletonScope)
        self.bind(LocationRepository, to_class=MongoLocationRepository, scope=SingletonScope)
        self.bind(LocationService, to_class=LocationServiceImpl, scope=SingletonScope)
