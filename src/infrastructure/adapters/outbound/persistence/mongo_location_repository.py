import re
from dataclasses import replace

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.location_repository import LocationRepository
from src.domain.models.location import Location
from src.infrastructure.adapters.outbound.persistence.location_persistence_mapper import LocationPersistenceMapper


class MongoLocationRepository(LocationRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    @staticmethod
    def _to_object_id(location_id: str) -> ObjectId | None:
        """Convert a string to an ObjectId, returning None if invalid."""
        try:
            return ObjectId(location_id)
        except InvalidId:
            return None

    async def save(self, location: Location) -> Location:
        doc = LocationPersistenceMapper.to_document(location)
        if location.id:
            oid = self._to_object_id(location.id)
            if oid is None:
                return location
            await self._collection.replace_one({"_id": oid}, doc, upsert=True)
            return location
        result = await self._collection.insert_one(doc)
        location.id = str(result.inserted_id)
        return location

    async def find_by_id(self, location_id: str) -> Location | None:
        oid = self._to_object_id(location_id)
        if oid is None:
            return None
        doc = await self._collection.find_one({"_id": oid})
        if doc is None:
            return None
        return LocationPersistenceMapper.to_domain(doc)

    async def find_all(self) -> list[Location]:
        docs = await self._collection.find().to_list(None)
        return [LocationPersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_type(self, location_type: str) -> list[Location]:
        docs = await self._collection.find({"location_type": location_type}).to_list(None)
        return [LocationPersistenceMapper.to_domain(doc) for doc in docs]

    async def find_children(self, parent_id: str) -> list[Location]:
        docs = await self._collection.find({"parent_id": parent_id}).to_list(None)
        return [LocationPersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_type_and_parent(self, location_type: str, parent_id: str) -> list[Location]:
        docs = await self._collection.find({"location_type": location_type, "parent_id": parent_id}).to_list(None)
        return [LocationPersistenceMapper.to_domain(doc) for doc in docs]

    async def update(self, location_id: str, location: Location) -> Location | None:
        oid = self._to_object_id(location_id)
        if oid is None:
            return None
        doc = LocationPersistenceMapper.to_document(location)
        result = await self._collection.replace_one({"_id": oid}, doc)
        if result.matched_count == 0:
            return None
        return replace(location, id=location_id)

    async def delete(self, location_id: str) -> bool:
        oid = self._to_object_id(location_id)
        if oid is None:
            return False
        result = await self._collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    async def search_by_name(self, query: str) -> list[Location]:
        docs = await self._collection.find({"name": {"$regex": re.escape(query), "$options": "i"}}).to_list(None)
        return [LocationPersistenceMapper.to_domain(doc) for doc in docs]

    async def find_ancestors(self, location_id: str) -> list[Location]:
        ancestors: list[Location] = []
        current = await self.find_by_id(location_id)
        if current is None:
            return ancestors
        ancestors.append(current)
        while current.parent_id is not None:
            parent = await self.find_by_id(current.parent_id)
            if parent is None or parent.location_type == "system":
                break
            ancestors.append(parent)
            current = parent
        return ancestors

    _KEY_FIELDS = ("location_type", "in_game")

    async def upsert_by_name(self, location: Location) -> tuple[Location, bool]:
        existing = await self._collection.find_one({"name": location.name})
        if existing is not None:
            doc = LocationPersistenceMapper.to_document(location)
            if not any(existing.get(f) != doc.get(f) for f in self._KEY_FIELDS):
                return LocationPersistenceMapper.to_domain(existing), False
        else:
            doc = LocationPersistenceMapper.to_document(location)
        result = await self._collection.find_one_and_update(
            {"name": location.name},
            {"$set": doc},
            upsert=True,
            return_document=True,
        )
        return LocationPersistenceMapper.to_domain(result), True
