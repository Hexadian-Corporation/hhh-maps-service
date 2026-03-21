from abc import ABC, abstractmethod

from src.domain.models.location_distance import LocationDistance


class LocationDistanceService(ABC):
    @abstractmethod
    async def create(self, distance: LocationDistance) -> LocationDistance: ...

    @abstractmethod
    async def get(self, distance_id: str) -> LocationDistance: ...

    @abstractmethod
    async def get_by_location(self, location_id: str) -> list[LocationDistance]: ...

    @abstractmethod
    async def get_by_pair(self, from_id: str, to_id: str) -> LocationDistance: ...

    @abstractmethod
    async def update(self, distance_id: str, distance: LocationDistance) -> LocationDistance: ...

    @abstractmethod
    async def delete(self, distance_id: str) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[LocationDistance]: ...

    @abstractmethod
    async def list_by_travel_type(self, travel_type: str) -> list[LocationDistance]: ...
