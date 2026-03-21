from abc import ABC, abstractmethod

from src.domain.models.location_distance import LocationDistance


class LocationDistanceRepository(ABC):
    @abstractmethod
    async def save(self, distance: LocationDistance) -> LocationDistance: ...

    @abstractmethod
    async def find_by_id(self, distance_id: str) -> LocationDistance | None: ...

    @abstractmethod
    async def find_by_location(self, location_id: str) -> list[LocationDistance]: ...

    @abstractmethod
    async def find_by_pair(self, from_id: str, to_id: str) -> LocationDistance | None: ...

    @abstractmethod
    async def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance | None: ...

    @abstractmethod
    async def delete(self, distance_id: str) -> bool: ...

    @abstractmethod
    async def find_all(self) -> list[LocationDistance]: ...

    @abstractmethod
    async def find_by_travel_type(self, travel_type: str) -> list[LocationDistance]: ...
