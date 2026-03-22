from abc import ABC, abstractmethod

from src.domain.models.location import Location


class LocationRepository(ABC):
    @abstractmethod
    async def save(self, location: Location) -> Location: ...

    @abstractmethod
    async def find_by_id(self, location_id: str) -> Location | None: ...

    @abstractmethod
    async def find_all(self) -> list[Location]: ...

    @abstractmethod
    async def find_by_type(self, location_type: str) -> list[Location]: ...

    @abstractmethod
    async def find_children(self, parent_id: str) -> list[Location]: ...

    @abstractmethod
    async def update(self, location_id: str, location: Location) -> Location | None: ...

    @abstractmethod
    async def delete(self, location_id: str) -> bool: ...

    @abstractmethod
    async def find_by_type_and_parent(self, location_type: str, parent_id: str) -> list[Location]: ...

    @abstractmethod
    async def search_by_name(self, query: str) -> list[Location]: ...

    @abstractmethod
    async def find_ancestors(self, location_id: str) -> list[Location]: ...

    @abstractmethod
    async def upsert_by_name(self, location: Location) -> tuple[Location, bool]: ...
