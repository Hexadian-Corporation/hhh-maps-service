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

    async def create(self, distance: LocationDistance) -> LocationDistance:
        result = await self._repository.save(distance)
        self._invalidate_cache()
        return result

    async def get(self, distance_id: str) -> LocationDistance:
        distance = await self._repository.find_by_id(distance_id)
        if distance is None:
            raise LocationDistanceNotFoundError(distance_id)
        return distance

    async def get_by_location(self, location_id: str) -> list[LocationDistance]:
        key = f"by_location:{location_id}"
        if key in self._cache:
            return cast(list[LocationDistance], self._cache[key])
        result = await self._repository.find_by_location(location_id)
        self._cache[key] = result
        return result

    async def get_by_pair(self, from_id: str, to_id: str) -> LocationDistance:
        pair = sorted([from_id, to_id])
        key = f"by_pair:{pair[0]}:{pair[1]}"
        if key in self._cache:
            return cast(LocationDistance, self._cache[key])
        distance = await self._repository.find_by_pair(from_id, to_id)
        if distance is None:
            raise LocationDistanceNotFoundError(f"{from_id} -> {to_id}")
        self._cache[key] = distance
        return distance

    async def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance:
        existing = await self._repository.find_by_id(distance_id)
        if existing is None:
            raise LocationDistanceNotFoundError(distance_id)
        updated = await self._repository.update(distance_id, distance)
        if updated is None:
            raise LocationDistanceNotFoundError(distance_id)
        self._invalidate_cache()
        return updated

    async def delete(self, distance_id: str) -> None:
        if not await self._repository.delete(distance_id):
            raise LocationDistanceNotFoundError(distance_id)
        self._invalidate_cache()

    async def list_all(self) -> list[LocationDistance]:
        return await self._repository.find_all()

    async def list_by_travel_type(self, travel_type: str) -> list[LocationDistance]:
        key = f"by_travel_type:{travel_type}"
        if key in self._cache:
            return cast(list[LocationDistance], self._cache[key])
        result = await self._repository.find_by_travel_type(travel_type)
        self._cache[key] = result
        return result
