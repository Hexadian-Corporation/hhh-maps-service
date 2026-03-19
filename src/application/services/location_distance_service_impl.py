from typing import cast

from cachetools import TTLCache

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.application.ports.outbound.location_distance_repository import LocationDistanceRepository
from src.domain.exceptions.location_distance_exceptions import LocationDistanceNotFoundError
from src.domain.models.location_distance import LocationDistance


class LocationDistanceServiceImpl(LocationDistanceService):
    def __init__(self, repository: LocationDistanceRepository) -> None:
        self._repository = repository
        self._cache: TTLCache[str, LocationDistance | list[LocationDistance]] = TTLCache(maxsize=512, ttl=300)

    def _invalidate_cache(self) -> None:
        self._cache.clear()

    def create(self, distance: LocationDistance) -> LocationDistance:
        result = self._repository.save(distance)
        self._invalidate_cache()
        return result

    def get(self, distance_id: str) -> LocationDistance:
        distance = self._repository.find_by_id(distance_id)
        if distance is None:
            raise LocationDistanceNotFoundError(distance_id)
        return distance

    def get_by_location(self, location_id: str) -> list[LocationDistance]:
        key = f"by_location:{location_id}"
        if key in self._cache:
            return cast(list[LocationDistance], self._cache[key])
        result = self._repository.find_by_location(location_id)
        self._cache[key] = result
        return result

    def get_by_pair(self, from_id: str, to_id: str) -> LocationDistance:
        pair = sorted([from_id, to_id])
        key = f"by_pair:{pair[0]}:{pair[1]}"
        if key in self._cache:
            return cast(LocationDistance, self._cache[key])
        distance = self._repository.find_by_pair(from_id, to_id)
        if distance is None:
            raise LocationDistanceNotFoundError(f"{from_id} -> {to_id}")
        self._cache[key] = distance
        return distance

    def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance:
        existing = self._repository.find_by_id(distance_id)
        if existing is None:
            raise LocationDistanceNotFoundError(distance_id)
        updated = self._repository.update(distance_id, distance)
        if updated is None:
            raise LocationDistanceNotFoundError(distance_id)
        self._invalidate_cache()
        return updated

    def delete(self, distance_id: str) -> None:
        if not self._repository.delete(distance_id):
            raise LocationDistanceNotFoundError(distance_id)
        self._invalidate_cache()
