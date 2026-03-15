"""Unit tests for LocationApiMapper.update_to_domain() and LocationUpdateDTO."""

from src.domain.models.location import Coordinates, Location
from src.infrastructure.adapters.inbound.api.location_api_mapper import LocationApiMapper
from src.infrastructure.adapters.inbound.api.location_dto import CoordinatesDTO, LocationUpdateDTO


class TestLocationUpdateDTO:
    """Validate LocationUpdateDTO defaults and partial field support."""

    def test_all_fields_default_to_none(self) -> None:
        dto = LocationUpdateDTO()
        assert dto.name is None
        assert dto.location_type is None
        assert dto.parent_id is None
        assert dto.coordinates is None
        assert dto.has_trade_terminal is None
        assert dto.has_landing_pad is None
        assert dto.landing_pad_size is None

    def test_partial_fields(self) -> None:
        dto = LocationUpdateDTO(name="New Name", has_trade_terminal=True)
        assert dto.name == "New Name"
        assert dto.has_trade_terminal is True
        assert dto.location_type is None

    def test_all_fields_set(self) -> None:
        dto = LocationUpdateDTO(
            name="Full",
            location_type="city",
            parent_id="p-1",
            coordinates=CoordinatesDTO(x=1.0, y=2.0, z=3.0),
            has_trade_terminal=True,
            has_landing_pad=False,
            landing_pad_size="small",
        )
        assert dto.name == "Full"
        assert dto.location_type == "city"
        assert dto.coordinates.x == 1.0


class TestUpdateToDomain:
    """Verify update_to_domain() merges partial DTO with existing Location."""

    @staticmethod
    def _make_existing() -> Location:
        return Location(
            id="loc-1",
            name="Port Olisar",
            location_type="station",
            parent_id="sys-1",
            coordinates=Coordinates(x=1.0, y=2.0, z=3.0),
            has_trade_terminal=True,
            has_landing_pad=True,
            landing_pad_size="large",
        )

    def test_empty_dto_preserves_existing(self) -> None:
        existing = self._make_existing()
        dto = LocationUpdateDTO()
        result = LocationApiMapper.update_to_domain(dto, existing)

        assert result.id == "loc-1"
        assert result.name == "Port Olisar"
        assert result.location_type == "station"
        assert result.parent_id == "sys-1"
        assert result.coordinates.x == 1.0
        assert result.has_trade_terminal is True
        assert result.has_landing_pad is True
        assert result.landing_pad_size == "large"

    def test_partial_update_name_only(self) -> None:
        existing = self._make_existing()
        dto = LocationUpdateDTO(name="New Name")
        result = LocationApiMapper.update_to_domain(dto, existing)

        assert result.name == "New Name"
        assert result.location_type == "station"
        assert result.parent_id == "sys-1"

    def test_partial_update_coordinates(self) -> None:
        existing = self._make_existing()
        dto = LocationUpdateDTO(coordinates=CoordinatesDTO(x=10.0, y=20.0, z=30.0))
        result = LocationApiMapper.update_to_domain(dto, existing)

        assert result.coordinates.x == 10.0
        assert result.coordinates.y == 20.0
        assert result.coordinates.z == 30.0

    def test_partial_update_booleans(self) -> None:
        existing = self._make_existing()
        dto = LocationUpdateDTO(has_trade_terminal=False)
        result = LocationApiMapper.update_to_domain(dto, existing)

        assert result.has_trade_terminal is False
        assert result.has_landing_pad is True

    def test_full_update_all_fields(self) -> None:
        existing = self._make_existing()
        dto = LocationUpdateDTO(
            name="Updated",
            location_type="city",
            parent_id="sys-2",
            coordinates=CoordinatesDTO(x=9.0, y=8.0, z=7.0),
            has_trade_terminal=False,
            has_landing_pad=False,
            landing_pad_size="small",
        )
        result = LocationApiMapper.update_to_domain(dto, existing)

        assert result.id == "loc-1"
        assert result.name == "Updated"
        assert result.location_type == "city"
        assert result.parent_id == "sys-2"
        assert result.coordinates.x == 9.0
        assert result.has_trade_terminal is False
        assert result.has_landing_pad is False
        assert result.landing_pad_size == "small"
