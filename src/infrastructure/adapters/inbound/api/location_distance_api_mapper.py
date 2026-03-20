from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.inbound.api.location_distance_dto import (
    LocationDistanceCreateDTO,
    LocationDistanceDTO,
    LocationDistanceUpdateDTO,
)


class LocationDistanceApiMapper:
    @staticmethod
    def create_to_domain(dto: LocationDistanceCreateDTO) -> LocationDistance:
        return LocationDistance(
            from_location_id=dto.from_location_id,
            to_location_id=dto.to_location_id,
            distance=dto.distance,
            travel_type=dto.travel_type,
            in_game=dto.in_game,
        )

    @staticmethod
    def to_dto(distance: LocationDistance) -> LocationDistanceDTO:
        return LocationDistanceDTO(
            _id=distance.id,
            from_location_id=distance.from_location_id,
            to_location_id=distance.to_location_id,
            distance=distance.distance,
            travel_type=distance.travel_type,
            in_game=distance.in_game,
        )

    @staticmethod
    def update_to_domain(dto: LocationDistanceUpdateDTO, existing: LocationDistance) -> LocationDistance:
        return LocationDistance(
            id=existing.id,
            from_location_id=dto.from_location_id if dto.from_location_id is not None else existing.from_location_id,
            to_location_id=dto.to_location_id if dto.to_location_id is not None else existing.to_location_id,
            distance=dto.distance if dto.distance is not None else existing.distance,
            travel_type=dto.travel_type if dto.travel_type is not None else existing.travel_type,
            in_game=dto.in_game if dto.in_game is not None else existing.in_game,
        )
