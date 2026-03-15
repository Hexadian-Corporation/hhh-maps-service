from abc import ABC, abstractmethod

from src.domain.models.location import Location


class LocationService(ABC):
    @abstractmethod
    def create(self, location: Location) -> Location: ...

    @abstractmethod
    def get(self, location_id: str) -> Location: ...

    @abstractmethod
    def list_all(self) -> list[Location]: ...

    @abstractmethod
    def list_by_type(self, location_type: str) -> list[Location]: ...

    @abstractmethod
    def list_children(self, parent_id: str) -> list[Location]: ...

    @abstractmethod
    def update(self, location_id: str, location: Location) -> Location: ...

    @abstractmethod
    def delete(self, location_id: str) -> None: ...
