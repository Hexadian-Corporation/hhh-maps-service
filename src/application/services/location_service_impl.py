from src.application.ports.inbound.location_service import LocationService
from src.application.ports.outbound.location_repository import LocationRepository
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Location


class LocationServiceImpl(LocationService):
    def __init__(self, repository: LocationRepository) -> None:
        self._repository = repository

    def create(self, location: Location) -> Location:
        return self._repository.save(location)

    def get(self, location_id: str) -> Location:
        location = self._repository.find_by_id(location_id)
        if location is None:
            raise LocationNotFoundError(location_id)
        return location

    def list_all(self) -> list[Location]:
        return self._repository.find_all()

    def list_by_type(self, location_type: str) -> list[Location]:
        return self._repository.find_by_type(location_type)

    def list_children(self, parent_id: str) -> list[Location]:
        return self._repository.find_children(parent_id)

    def update(self, location_id: str, location: Location) -> Location:
        existing = self._repository.find_by_id(location_id)
        if existing is None:
            raise LocationNotFoundError(location_id)
        updated = self._repository.update(location_id, location)
        if updated is None:
            raise LocationNotFoundError(location_id)
        return updated

    def delete(self, location_id: str) -> None:
        if not self._repository.delete(location_id):
            raise LocationNotFoundError(location_id)

    def search_by_name(self, query: str) -> list[Location]:
        if not query:
            return []
        return self._repository.search_by_name(query)
