from cachetools import TTLCache

from src.application.ports.inbound.location_service import LocationService
from src.application.ports.outbound.location_repository import LocationRepository
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Location


class LocationServiceImpl(LocationService):
    def __init__(self, repository: LocationRepository) -> None:
        self._repository = repository
        self._cache: TTLCache[str, list[Location]] = TTLCache(maxsize=256, ttl=300)

    def _invalidate_cache(self) -> None:
        self._cache.clear()

    async def create(self, location: Location) -> Location:
        result = await self._repository.save(location)
        self._invalidate_cache()
        return result

    async def get(self, location_id: str) -> Location:
        location = await self._repository.find_by_id(location_id)
        if location is None:
            raise LocationNotFoundError(location_id)
        return location

    async def list_all(self) -> list[Location]:
        key = "list_all"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.find_all()
        self._cache[key] = result
        return result

    async def list_by_type(self, location_type: str) -> list[Location]:
        key = f"list_by_type:{location_type}"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.find_by_type(location_type)
        self._cache[key] = result
        return result

    async def list_children(self, parent_id: str) -> list[Location]:
        key = f"list_children:{parent_id}"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.find_children(parent_id)
        self._cache[key] = result
        return result

    async def list_by_type_and_parent(self, location_type: str, parent_id: str) -> list[Location]:
        key = f"list_by_type_and_parent:{location_type}:{parent_id}"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.find_by_type_and_parent(location_type, parent_id)
        self._cache[key] = result
        return result

    async def update(self, location_id: str, location: Location) -> Location:
        existing = await self._repository.find_by_id(location_id)
        if existing is None:
            raise LocationNotFoundError(location_id)
        updated = await self._repository.update(location_id, location)
        if updated is None:
            raise LocationNotFoundError(location_id)
        self._invalidate_cache()
        return updated

    async def delete(self, location_id: str) -> None:
        if not await self._repository.delete(location_id):
            raise LocationNotFoundError(location_id)
        self._invalidate_cache()

    async def search_by_name(self, query: str) -> list[Location]:
        if not query:
            return []
        key = f"search_by_name:{query}"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.search_by_name(query)
        self._cache[key] = result
        return result

    async def get_ancestors(self, location_id: str) -> list[Location]:
        location = await self._repository.find_by_id(location_id)
        if location is None:
            raise LocationNotFoundError(location_id)
        key = f"get_ancestors:{location_id}"
        if key in self._cache:
            return self._cache[key]
        result = await self._repository.find_ancestors(location_id)
        self._cache[key] = result
        return result
