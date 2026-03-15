"""Unit tests for src.seed – seed data definitions and insertion logic."""

import dataclasses
from unittest.mock import MagicMock

from src.domain.models.location import Coordinates, Location
from src.seed import _LOCATION_DEFS, SYSTEMS, build_locations, seed_locations

# ---------------------------------------------------------------------------
# Tests for seed data definitions
# ---------------------------------------------------------------------------


class TestSeedDataDefinitions:
    """Validate the static seed data meets the issue requirements."""

    def test_systems_count(self) -> None:
        assert len(SYSTEMS) == 2

    def test_system_names(self) -> None:
        names = {s.name for s in SYSTEMS}
        assert names == {"Stanton", "Pyro"}

    def test_systems_have_correct_type(self) -> None:
        for system in SYSTEMS:
            assert system.location_type == "system"

    def test_systems_have_no_id(self) -> None:
        for system in SYSTEMS:
            assert system.id is None

    def test_location_defs_count(self) -> None:
        """At least 9 test locations as required by the issue."""
        assert len(_LOCATION_DEFS) >= 9

    def test_location_def_names(self) -> None:
        names = {defn[0] for defn in _LOCATION_DEFS}
        expected = {
            "Port Olisar",
            "Area18",
            "Lorville",
            "New Babbage",
            "GrimHEX",
            "CRU-L1",
            "HUR-L1",
            "Ruin Station",
            "Pyro Gateway",
        }
        assert expected <= names

    def test_location_def_types(self) -> None:
        types = {defn[2] for defn in _LOCATION_DEFS}
        assert types == {"orbital", "city", "station"}

    def test_location_def_systems(self) -> None:
        systems = {defn[1] for defn in _LOCATION_DEFS}
        assert systems == {"Stanton", "Pyro"}

    def test_stanton_locations_count(self) -> None:
        stanton = [d for d in _LOCATION_DEFS if d[1] == "Stanton"]
        assert len(stanton) == 7

    def test_pyro_locations_count(self) -> None:
        pyro = [d for d in _LOCATION_DEFS if d[1] == "Pyro"]
        assert len(pyro) == 2


# ---------------------------------------------------------------------------
# Tests for build_locations()
# ---------------------------------------------------------------------------


class TestBuildLocations:
    """Verify build_locations() resolves parent IDs correctly."""

    def test_returns_correct_count(self) -> None:
        system_ids = {"Stanton": "s1", "Pyro": "p1"}
        locations = build_locations(system_ids)
        assert len(locations) == len(_LOCATION_DEFS)

    def test_parent_ids_are_resolved(self) -> None:
        system_ids = {"Stanton": "s1", "Pyro": "p1"}
        locations = build_locations(system_ids)
        for loc in locations:
            assert loc.parent_id in ("s1", "p1")

    def test_stanton_children_get_stanton_id(self) -> None:
        system_ids = {"Stanton": "stan-id", "Pyro": "pyro-id"}
        locations = build_locations(system_ids)
        stanton_children = [loc for loc in locations if loc.parent_id == "stan-id"]
        assert len(stanton_children) == 7
        expected_names = {"Port Olisar", "Area18", "Lorville", "New Babbage", "GrimHEX", "CRU-L1", "HUR-L1"}
        assert {loc.name for loc in stanton_children} == expected_names

    def test_pyro_children_get_pyro_id(self) -> None:
        system_ids = {"Stanton": "stan-id", "Pyro": "pyro-id"}
        locations = build_locations(system_ids)
        pyro_children = [loc for loc in locations if loc.parent_id == "pyro-id"]
        assert len(pyro_children) == 2
        assert {loc.name for loc in pyro_children} == {"Ruin Station", "Pyro Gateway"}

    def test_location_fields_populated(self) -> None:
        system_ids = {"Stanton": "s1", "Pyro": "p1"}
        locations = build_locations(system_ids)
        for loc in locations:
            assert loc.name != ""
            assert loc.location_type in ("orbital", "city", "station")
            assert isinstance(loc.coordinates, Coordinates)
            assert isinstance(loc.has_trade_terminal, bool)
            assert isinstance(loc.has_landing_pad, bool)

    def test_locations_have_no_id(self) -> None:
        system_ids = {"Stanton": "s1", "Pyro": "p1"}
        locations = build_locations(system_ids)
        for loc in locations:
            assert loc.id is None


# ---------------------------------------------------------------------------
# Tests for seed_locations()
# ---------------------------------------------------------------------------


class TestSeedLocations:
    """Verify seed_locations() orchestrates system + location creation."""

    @staticmethod
    def _make_service() -> MagicMock:
        """Return a mock LocationService whose ``create`` returns a copy with a fake ID."""
        service = MagicMock()
        call_counter = {"n": 0}

        def fake_create(location: Location) -> Location:
            call_counter["n"] += 1
            return dataclasses.replace(location, id=f"id-{call_counter['n']}")

        service.create.side_effect = fake_create
        service.list_by_type.return_value = []
        return service

    def test_returns_all_created_locations(self) -> None:
        service = self._make_service()
        result = seed_locations(service)
        # 2 systems + 9 locations = 11 total
        assert len(result) == len(SYSTEMS) + len(_LOCATION_DEFS)

    def test_service_create_called_for_each(self) -> None:
        service = self._make_service()
        seed_locations(service)
        expected_calls = len(SYSTEMS) + len(_LOCATION_DEFS)
        assert service.create.call_count == expected_calls

    def test_systems_created_first(self) -> None:
        service = self._make_service()
        seed_locations(service)
        calls = service.create.call_args_list
        # First two calls should be copies of the system locations
        first_arg = calls[0][0][0]
        second_arg = calls[1][0][0]
        assert first_arg.name == SYSTEMS[0].name
        assert first_arg.location_type == SYSTEMS[0].location_type
        assert second_arg.name == SYSTEMS[1].name
        assert second_arg.location_type == SYSTEMS[1].location_type

    def test_child_locations_have_parent_ids(self) -> None:
        service = self._make_service()
        result = seed_locations(service)
        # Skip the first 2 (systems); remaining should have parent_id set
        child_locations = result[len(SYSTEMS) :]
        for loc in child_locations:
            assert loc.parent_id is not None

    def test_all_returned_locations_have_ids(self) -> None:
        service = self._make_service()
        result = seed_locations(service)
        for loc in result:
            assert loc.id is not None

    def test_idempotent_skips_when_systems_exist(self) -> None:
        """seed_locations returns [] and creates nothing when systems already exist."""
        service = self._make_service()
        service.list_by_type.return_value = [
            Location(id="existing-1", name="Stanton", location_type="system"),
        ]
        result = seed_locations(service)
        assert result == []
        service.create.assert_not_called()

    def test_idempotent_checks_system_type(self) -> None:
        """seed_locations queries list_by_type('system') for the guard."""
        service = self._make_service()
        seed_locations(service)
        service.list_by_type.assert_called_once_with("system")
