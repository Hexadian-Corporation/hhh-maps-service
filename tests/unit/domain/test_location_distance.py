"""Unit tests for LocationDistance domain model and LocationDistanceNotFoundError."""

import pytest

from src.domain.exceptions.location_distance_exceptions import LocationDistanceNotFoundError
from src.domain.models.location_distance import LocationDistance


class TestLocationDistance:
    """Verify LocationDistance dataclass defaults and field assignment."""

    def test_defaults(self) -> None:
        ld = LocationDistance()
        assert ld.id is None
        assert ld.from_location_id == ""
        assert ld.to_location_id == ""
        assert ld.distance == 0.0
        assert ld.travel_type == ""

    def test_all_fields_set(self) -> None:
        ld = LocationDistance(
            id="dist-1",
            from_location_id="loc-a",
            to_location_id="loc-b",
            distance=1500.0,
            travel_type="quantum",
        )
        assert ld.id == "dist-1"
        assert ld.from_location_id == "loc-a"
        assert ld.to_location_id == "loc-b"
        assert ld.distance == 1500.0
        assert ld.travel_type == "quantum"

    def test_partial_fields(self) -> None:
        ld = LocationDistance(from_location_id="loc-x", distance=42.5)
        assert ld.from_location_id == "loc-x"
        assert ld.distance == 42.5
        assert ld.to_location_id == ""
        assert ld.travel_type == ""

    def test_equality(self) -> None:
        a = LocationDistance(id="d1", from_location_id="x", to_location_id="y", distance=10.0, travel_type="scm")
        b = LocationDistance(id="d1", from_location_id="x", to_location_id="y", distance=10.0, travel_type="scm")
        assert a == b

    def test_inequality(self) -> None:
        a = LocationDistance(id="d1")
        b = LocationDistance(id="d2")
        assert a != b


class TestLocationDistanceNotFoundError:
    """Verify LocationDistanceNotFoundError message and attribute."""

    def test_message(self) -> None:
        err = LocationDistanceNotFoundError("dist-99")
        assert str(err) == "Location distance not found: dist-99"

    def test_distance_id_attribute(self) -> None:
        err = LocationDistanceNotFoundError("abc")
        assert err.distance_id == "abc"

    def test_is_exception(self) -> None:
        with pytest.raises(LocationDistanceNotFoundError):
            raise LocationDistanceNotFoundError("x")
