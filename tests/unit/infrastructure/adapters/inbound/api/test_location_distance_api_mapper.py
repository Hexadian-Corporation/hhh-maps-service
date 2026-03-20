"""Unit tests for LocationDistanceApiMapper."""

from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.inbound.api.location_distance_api_mapper import LocationDistanceApiMapper
from src.infrastructure.adapters.inbound.api.location_distance_dto import (
    LocationDistanceCreateDTO,
    LocationDistanceUpdateDTO,
)


def _make_distance(distance_id: str = "d-1") -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id="loc-a",
        to_location_id="loc-b",
        distance=1500.0,
        travel_type="quantum",
        in_game=True,
    )


class TestCreateToDomain:
    def test_creates_domain_without_id(self) -> None:
        dto = LocationDistanceCreateDTO(
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=1500.0,
            travel_type="quantum",
        )
        result = LocationDistanceApiMapper.create_to_domain(dto)
        assert result.id is None
        assert result.from_location_id == "loc-a"
        assert result.to_location_id == "loc-b"
        assert result.distance == 1500.0
        assert result.travel_type == "quantum"
        assert result.in_game is True

    def test_creates_domain_with_in_game_false(self) -> None:
        dto = LocationDistanceCreateDTO(
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=1500.0,
            travel_type="quantum",
            in_game=False,
        )
        result = LocationDistanceApiMapper.create_to_domain(dto)
        assert result.in_game is False


class TestToDto:
    def test_maps_all_fields(self) -> None:
        domain = _make_distance()
        dto = LocationDistanceApiMapper.to_dto(domain)
        assert dto.id == "d-1"
        assert dto.from_location_id == "loc-a"
        assert dto.to_location_id == "loc-b"
        assert dto.distance == 1500.0
        assert dto.travel_type == "quantum"
        assert dto.in_game is True

    def test_maps_none_id(self) -> None:
        domain = LocationDistance(
            id=None,
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=200.0,
            travel_type="scm",
        )
        dto = LocationDistanceApiMapper.to_dto(domain)
        assert dto.id is None

    def test_maps_in_game_false(self) -> None:
        domain = LocationDistance(
            id="d-2",
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=200.0,
            travel_type="scm",
            in_game=False,
        )
        dto = LocationDistanceApiMapper.to_dto(domain)
        assert dto.in_game is False


class TestUpdateToDomain:
    def test_full_update(self) -> None:
        existing = _make_distance()
        dto = LocationDistanceUpdateDTO(
            from_location_id="loc-x",
            to_location_id="loc-y",
            distance=999.0,
            travel_type="on_foot",
            in_game=False,
        )
        result = LocationDistanceApiMapper.update_to_domain(dto, existing)
        assert result.id == "d-1"
        assert result.from_location_id == "loc-x"
        assert result.to_location_id == "loc-y"
        assert result.distance == 999.0
        assert result.travel_type == "on_foot"
        assert result.in_game is False

    def test_partial_update_preserves_existing(self) -> None:
        existing = _make_distance()
        dto = LocationDistanceUpdateDTO(distance=500.0)
        result = LocationDistanceApiMapper.update_to_domain(dto, existing)
        assert result.from_location_id == "loc-a"
        assert result.to_location_id == "loc-b"
        assert result.distance == 500.0
        assert result.travel_type == "quantum"
        assert result.in_game is True

    def test_empty_update_preserves_all(self) -> None:
        existing = _make_distance()
        dto = LocationDistanceUpdateDTO()
        result = LocationDistanceApiMapper.update_to_domain(dto, existing)
        assert result.from_location_id == "loc-a"
        assert result.to_location_id == "loc-b"
        assert result.distance == 1500.0
        assert result.travel_type == "quantum"
        assert result.in_game is True

    def test_update_in_game_only(self) -> None:
        existing = _make_distance()
        dto = LocationDistanceUpdateDTO(in_game=False)
        result = LocationDistanceApiMapper.update_to_domain(dto, existing)
        assert result.in_game is False
        assert result.from_location_id == "loc-a"
        assert result.distance == 1500.0
