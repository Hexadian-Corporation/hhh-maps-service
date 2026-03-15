from abc import ABC, abstractmethod

from src.domain.models.location import Location


class LocationRepository(ABC):
    @abstractmethod
    def save(self, location: Location) -> Location: ...

    @abstractmethod
    def find_by_id(self, location_id: str) -> Location | None: ...

    @abstractmethod
    def find_all(self) -> list[Location]: ...

    @abstractmethod
    def find_by_type(self, location_type: str) -> list[Location]: ...

    @abstractmethod
    def find_children(self, parent_id: str) -> list[Location]: ...

    @abstractmethod
    def delete(self, location_id: str) -> bool: ...

    @abstractmethod
    def search_by_name(self, query: str) -> list[Location]: ...
