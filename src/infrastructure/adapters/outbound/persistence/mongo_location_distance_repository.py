from dataclasses import replace

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.location_distance_repository import LocationDistanceRepository
from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.outbound.persistence.location_distance_persistence_mapper import (
    LocationDistancePersistenceMapper,
)


class MongoLocationDistanceRepository(LocationDistanceRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def save(self, distance: LocationDistance) -> LocationDistance:
        normalized = self._normalize_pair(distance)
        doc = LocationDistancePersistenceMapper.to_document(normalized)
        if distance.id:
            await self._collection.replace_one({"_id": ObjectId(distance.id)}, doc, upsert=True)
            return normalized
        result = await self._collection.insert_one(doc)
        return replace(normalized, id=str(result.inserted_id))

    async def find_by_id(self, distance_id: str) -> LocationDistance | None:
        doc = await self._collection.find_one({"_id": ObjectId(distance_id)})
        if doc is None:
            return None
        return LocationDistancePersistenceMapper.to_domain(doc)

    async def find_by_location(self, location_id: str) -> list[LocationDistance]:
        docs = await self._collection.find(
            {
                "$or": [
                    {"from_location_id": location_id},
                    {"to_location_id": location_id},
                ]
            }
        ).to_list(None)
        return [LocationDistancePersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_pair(self, from_id: str, to_id: str) -> LocationDistance | None:
        pair = sorted([from_id, to_id])
        doc = await self._collection.find_one(
            {
                "from_location_id": pair[0],
                "to_location_id": pair[1],
            }
        )
        if doc is None:
            return None
        return LocationDistancePersistenceMapper.to_domain(doc)

    async def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance | None:
        normalized = self._normalize_pair(distance)
        doc = LocationDistancePersistenceMapper.to_document(normalized)
        result = await self._collection.replace_one({"_id": ObjectId(distance_id)}, doc)
        if result.matched_count == 0:
            return None
        return replace(normalized, id=distance_id)

    async def delete(self, distance_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(distance_id)})
        return result.deleted_count > 0

    async def find_all(self) -> list[LocationDistance]:
        docs = await self._collection.find({}).to_list(None)
        return [LocationDistancePersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_travel_type(self, travel_type: str) -> list[LocationDistance]:
        docs = await self._collection.find({"travel_type": travel_type}).to_list(None)
        return [LocationDistancePersistenceMapper.to_domain(doc) for doc in docs]

    _KEY_FIELDS = ("distance",)

    async def upsert_by_pair(self, distance: LocationDistance) -> tuple[LocationDistance, bool]:
        normalized = self._normalize_pair(distance)
        query = {
            "from_location_id": normalized.from_location_id,
            "to_location_id": normalized.to_location_id,
            "travel_type": normalized.travel_type,
        }
        existing = await self._collection.find_one(query)
        if existing is not None:
            doc = LocationDistancePersistenceMapper.to_document(normalized)
            if not any(existing.get(f) != doc.get(f) for f in self._KEY_FIELDS):
                return LocationDistancePersistenceMapper.to_domain(existing), False
        else:
            doc = LocationDistancePersistenceMapper.to_document(normalized)
        result = await self._collection.find_one_and_update(
            query,
            {"$set": doc},
            upsert=True,
            return_document=True,
        )
        return LocationDistancePersistenceMapper.to_domain(result), True

    @staticmethod
    def _normalize_pair(distance: LocationDistance) -> LocationDistance:
        """Ensure from_location_id < to_location_id for consistent pair storage."""
        if distance.from_location_id > distance.to_location_id:
            return replace(
                distance,
                from_location_id=distance.to_location_id,
                to_location_id=distance.from_location_id,
            )
        return distance
