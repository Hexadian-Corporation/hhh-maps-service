from dataclasses import replace

from bson import ObjectId
from pymongo.collection import Collection

from src.application.ports.outbound.location_distance_repository import LocationDistanceRepository
from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.outbound.persistence.location_distance_persistence_mapper import (
    LocationDistancePersistenceMapper,
)


class MongoLocationDistanceRepository(LocationDistanceRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, distance: LocationDistance) -> LocationDistance:
        normalized = self._normalize_pair(distance)
        doc = LocationDistancePersistenceMapper.to_document(normalized)
        if distance.id:
            self._collection.replace_one({"_id": ObjectId(distance.id)}, doc, upsert=True)
            return normalized
        result = self._collection.insert_one(doc)
        return replace(normalized, id=str(result.inserted_id))

    def find_by_id(self, distance_id: str) -> LocationDistance | None:
        doc = self._collection.find_one({"_id": ObjectId(distance_id)})
        if doc is None:
            return None
        return LocationDistancePersistenceMapper.to_domain(doc)

    def find_by_location(self, location_id: str) -> list[LocationDistance]:
        cursor = self._collection.find(
            {
                "$or": [
                    {"from_location_id": location_id},
                    {"to_location_id": location_id},
                ]
            }
        )
        return [LocationDistancePersistenceMapper.to_domain(doc) for doc in cursor]

    def find_by_pair(self, from_id: str, to_id: str) -> LocationDistance | None:
        pair = sorted([from_id, to_id])
        doc = self._collection.find_one(
            {
                "from_location_id": pair[0],
                "to_location_id": pair[1],
            }
        )
        if doc is None:
            return None
        return LocationDistancePersistenceMapper.to_domain(doc)

    def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance | None:
        normalized = self._normalize_pair(distance)
        doc = LocationDistancePersistenceMapper.to_document(normalized)
        result = self._collection.replace_one({"_id": ObjectId(distance_id)}, doc)
        if result.matched_count == 0:
            return None
        return replace(normalized, id=distance_id)

    def delete(self, distance_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(distance_id)})
        return result.deleted_count > 0

    def find_all(self) -> list[LocationDistance]:
        cursor = self._collection.find({})
        return [LocationDistancePersistenceMapper.to_domain(doc) for doc in cursor]

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
