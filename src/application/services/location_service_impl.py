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

    def create(self, location: Location) -> Location:
        result = self._repository.save(location)
        self._invalidate_cache()
        return result

    def get(self, location_id: str) -> Location:
        location = self._repository.find_by_id(location_id)
        if location is None:
            raise LocationNotFoundError(location_id)
        return location

    def list_all(self) -> list[Location]:
        key = "list_all"
        if key in self._cache:
            return self._cache[key]
        result = self._repository.find_all()
        self._cache[key] = result
        return result

    def list_by_type(self, location_type: str) -> list[Location]:
        key = f"list_by_type:{location_type}"
        if key in self._cache:
            return self._cache[key]
        result = self._repository.find_by_type(location_type)
        self._cache[key] = result
        return result

    def list_children(self, parent_id: str) -> list[Location]:
        key = f"list_children:{parent_id}"
        if key in self._cache:
            return self._cache[key]
        result = self._repository.find_children(parent_id)
        self._cache[key] = result
        return result

    def list_by_type_and_parent(self, location_type: str, parent_id: str) -> list[Location]:
        key = f"list_by_type_and_parent:{location_type}:{parent_id}"
        if key in self._cache:
            return self._cache[key]
        result = self._repository.find_by_type_and_parent(location_type, parent_id)
        self._cache[key] = result
        return result

    def update(self, location_id: str, location: Location) -> Location:
        existing = self._repository.find_by_id(location_id)
        if existing is None:
            raise LocationNotFoundError(location_id)
        updated = self._repository.update(location_id, location)
        if updated is None:
            raise LocationNotFoundError(location_id)
        self._invalidate_cache()
        return updated

    def delete(self, location_id: str) -> None:
        if not self._repository.delete(location_id):
            raise LocationNotFoundError(location_id)
        self._invalidate_cache()

    def search_by_name(self, query: str) -> list[Location]:
        if not query:
            return []
        key = f"search_by_name:{query}"
        if key in self._cache:
            return self._cache[key]
        result = self._repository.search_by_name(query)
        self._cache[key] = result
        return result
