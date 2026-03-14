from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_dto import CoordinatesDTO, LocationDTO


class LocationApiMapper:

    @staticmethod
    def to_domain(dto: LocationDTO) -> Location:
        return Location(
            id=dto.id,
            name=dto.name,
            location_type=dto.location_type,
            parent_id=dto.parent_id,
            coordinates=Coordinates(x=dto.coordinates.x, y=dto.coordinates.y, z=dto.coordinates.z),
            has_trade_terminal=dto.has_trade_terminal,
            has_landing_pad=dto.has_landing_pad,
            landing_pad_size=dto.landing_pad_size,
        )

    @staticmethod
    def to_dto(location: Location) -> LocationDTO:
        return LocationDTO(
            _id=location.id,
            name=location.name,
            location_type=location.location_type,
            parent_id=location.parent_id,
            coordinates=CoordinatesDTO(
                x=location.coordinates.x,
                y=location.coordinates.y,
                z=location.coordinates.z,
            ),
            has_trade_terminal=location.has_trade_terminal,
            has_landing_pad=location.has_landing_pad,
            landing_pad_size=location.landing_pad_size,
        )
