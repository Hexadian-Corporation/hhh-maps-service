from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_dto import CoordinatesDTO, LocationDTO, LocationUpdateDTO


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

    @staticmethod
    def update_to_domain(dto: LocationUpdateDTO, existing: Location) -> Location:
        coordinates = existing.coordinates
        if dto.coordinates is not None:
            coordinates = Coordinates(x=dto.coordinates.x, y=dto.coordinates.y, z=dto.coordinates.z)
        has_trade_terminal = (
            dto.has_trade_terminal if dto.has_trade_terminal is not None else existing.has_trade_terminal
        )
        has_landing_pad = dto.has_landing_pad if dto.has_landing_pad is not None else existing.has_landing_pad
        landing_pad_size = dto.landing_pad_size if dto.landing_pad_size is not None else existing.landing_pad_size
        return Location(
            id=existing.id,
            name=dto.name if dto.name is not None else existing.name,
            location_type=dto.location_type if dto.location_type is not None else existing.location_type,
            parent_id=dto.parent_id if dto.parent_id is not None else existing.parent_id,
            coordinates=coordinates,
            has_trade_terminal=has_trade_terminal,
            has_landing_pad=has_landing_pad,
            landing_pad_size=landing_pad_size,
        )
