from bson import ObjectId
from pymongo.collection import Collection

from src.application.ports.outbound.location_repository import LocationRepository
from src.domain.models.location import Location
from src.infrastructure.adapters.outbound.persistence.location_persistence_mapper import LocationPersistenceMapper


class MongoLocationRepository(LocationRepository):

    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, location: Location) -> Location:
        doc = LocationPersistenceMapper.to_document(location)
        if location.id:
            self._collection.replace_one({"_id": ObjectId(location.id)}, doc, upsert=True)
            return location
        result = self._collection.insert_one(doc)
        location.id = str(result.inserted_id)
        return location

    def find_by_id(self, location_id: str) -> Location | None:
        doc = self._collection.find_one({"_id": ObjectId(location_id)})
        if doc is None:
            return None
        return LocationPersistenceMapper.to_domain(doc)

    def find_all(self) -> list[Location]:
        return [LocationPersistenceMapper.to_domain(doc) for doc in self._collection.find()]

    def find_by_type(self, location_type: str) -> list[Location]:
        return [
            LocationPersistenceMapper.to_domain(doc)
            for doc in self._collection.find({"location_type": location_type})
        ]

    def find_children(self, parent_id: str) -> list[Location]:
        return [
            LocationPersistenceMapper.to_domain(doc)
            for doc in self._collection.find({"parent_id": parent_id})
        ]

    def delete(self, location_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(location_id)})
        return result.deleted_count > 0

    def search_by_name(self, query: str) -> list[Location]:
        cursor = self._collection.find({"name": {"$regex": query, "$options": "i"}})
        return [LocationPersistenceMapper.to_domain(doc) for doc in cursor]
