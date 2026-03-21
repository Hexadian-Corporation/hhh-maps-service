from abc import ABC, abstractmethod

from src.domain.models.location import Location


class LocationService(ABC):
    @abstractmethod
    async def create(self, location: Location) -> Location: ...

    @abstractmethod
    async def get(self, location_id: str) -> Location: ...

    @abstractmethod
    async def list_all(self) -> list[Location]: ...

    @abstractmethod
    async def list_by_type(self, location_type: str) -> list[Location]: ...

    @abstractmethod
    async def list_children(self, parent_id: str) -> list[Location]: ...

    @abstractmethod
    async def list_by_type_and_parent(self, location_type: str, parent_id: str) -> list[Location]: ...

    @abstractmethod
    async def update(self, location_id: str, location: Location) -> Location: ...

    @abstractmethod
    async def delete(self, location_id: str) -> None: ...

    @abstractmethod
    async def search_by_name(self, query: str) -> list[Location]: ...

    @abstractmethod
    async def get_ancestors(self, location_id: str) -> list[Location]: ...
