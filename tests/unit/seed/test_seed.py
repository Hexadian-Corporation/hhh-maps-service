"""Unit tests for src.seed – seed data definitions and insertion logic."""

import dataclasses
import math
from unittest.mock import AsyncMock

import pytest

from src.domain.models.location import Location
from src.domain.models.location_distance import LocationDistance
from src.seed import (
    _LOCATION_COORDS,
    _LOCATION_DEFS,
    SYSTEMS,
    build_locations,
    compute_distance,
    seed_distances,
    seed_locations,
)

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
    def _make_service() -> AsyncMock:
        """Return a mock LocationService whose ``create`` returns a copy with a fake ID."""
        service = AsyncMock()
        call_counter = {"n": 0}

        async def fake_create(location: Location) -> Location:
            call_counter["n"] += 1
            return dataclasses.replace(location, id=f"id-{call_counter['n']}")

        service.create.side_effect = fake_create
        service.list_by_type.return_value = []
        return service

    @pytest.mark.anyio
    async def test_returns_all_created_locations(self) -> None:
        service = self._make_service()
        result = await seed_locations(service)
        # 2 systems + 9 locations = 11 total
        assert len(result) == len(SYSTEMS) + len(_LOCATION_DEFS)

    @pytest.mark.anyio
    async def test_service_create_called_for_each(self) -> None:
        service = self._make_service()
        await seed_locations(service)
        expected_calls = len(SYSTEMS) + len(_LOCATION_DEFS)
        assert service.create.call_count == expected_calls

    @pytest.mark.anyio
    async def test_systems_created_first(self) -> None:
        service = self._make_service()
        result = await seed_locations(service)
        # First two results should be the systems
        assert result[0].location_type == "system"
        assert result[1].location_type == "system"
        system_names = {result[0].name, result[1].name}
        assert system_names == {"Stanton", "Pyro"}

    @pytest.mark.anyio
    async def test_child_locations_have_parent_ids(self) -> None:
        service = self._make_service()
        result = await seed_locations(service)
        # Skip the first 2 (systems); remaining should have parent_id set
        child_locations = result[len(SYSTEMS) :]
        for loc in child_locations:
            assert loc.parent_id is not None

    @pytest.mark.anyio
    async def test_all_returned_locations_have_ids(self) -> None:
        service = self._make_service()
        result = await seed_locations(service)
        for loc in result:
            assert loc.id is not None

    @pytest.mark.anyio
    async def test_idempotent_skips_when_systems_exist(self) -> None:
        """seed_locations returns [] and creates nothing when systems already exist."""
        service = self._make_service()
        service.list_by_type.return_value = [
            Location(id="existing-1", name="Stanton", location_type="system"),
        ]
        result = await seed_locations(service)
        assert result == []
        service.create.assert_not_called()

    @pytest.mark.anyio
    async def test_idempotent_checks_system_type(self) -> None:
        """seed_locations queries list_by_type('system') for the guard."""
        service = self._make_service()
        await seed_locations(service)
        service.list_by_type.assert_called_once_with("system")


# ---------------------------------------------------------------------------
# Tests for seed_distances()
# ---------------------------------------------------------------------------


class TestSeedDistances:
    """Verify seed_distances() computes and creates pairwise distances."""

    @staticmethod
    def _make_location_service(trade_locations: list[Location]) -> AsyncMock:
        service = AsyncMock()
        service.list_all.return_value = trade_locations
        return service

    @staticmethod
    def _make_distance_service(existing: list[LocationDistance] | None = None) -> AsyncMock:
        service = AsyncMock()
        service.list_all.return_value = existing or []
        call_counter = {"n": 0}

        async def fake_create(ld: LocationDistance) -> LocationDistance:
            call_counter["n"] += 1
            return dataclasses.replace(ld, id=f"dist-{call_counter['n']}")

        service.create.side_effect = fake_create
        return service

    @staticmethod
    def _make_trade_locations(names: list[str]) -> list[Location]:
        return [
            Location(id=f"loc-{i}", name=name, location_type="station", has_trade_terminal=True)
            for i, name in enumerate(names)
        ]

    @pytest.mark.anyio
    async def test_computes_pairwise_distances(self) -> None:
        """Correct number of records created for N trade-terminal locations."""
        names = list(_LOCATION_COORDS.keys())[:3]  # 3 locations → 3 pairs × 2 types = 6 records
        trade_locs = self._make_trade_locations(names)
        loc_svc = self._make_location_service(trade_locs)
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        n = len(trade_locs)
        expected = n * (n - 1) // 2 * 2  # pairs × 2 travel types
        assert len(result) == expected

    @pytest.mark.anyio
    async def test_idempotent_when_distances_exist(self) -> None:
        """Returns [] and creates nothing when distances already exist."""
        existing = [
            LocationDistance(id="d1", from_location_id="a", to_location_id="b", distance=1.0, travel_type="quantum")
        ]
        loc_svc = self._make_location_service([])
        dist_svc = self._make_distance_service(existing)

        result = await seed_distances(loc_svc, dist_svc)

        assert result == []
        dist_svc.create.assert_not_called()

    @pytest.mark.anyio
    async def test_creates_quantum_and_scm_records_per_pair(self) -> None:
        """Each unique pair produces one quantum and one scm record."""
        names = list(_LOCATION_COORDS.keys())[:2]
        trade_locs = self._make_trade_locations(names)
        loc_svc = self._make_location_service(trade_locs)
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        travel_types = [r.travel_type for r in result]
        assert travel_types.count("quantum") == 1
        assert travel_types.count("scm") == 1

    @pytest.mark.anyio
    async def test_distance_values_are_positive(self) -> None:
        """All computed distances are > 0."""
        names = list(_LOCATION_COORDS.keys())[:3]
        trade_locs = self._make_trade_locations(names)
        loc_svc = self._make_location_service(trade_locs)
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        for record in result:
            assert record.distance > 0

    @pytest.mark.anyio
    async def test_only_trade_locations_included(self) -> None:
        """Non-trade-terminal locations are excluded."""
        names = list(_LOCATION_COORDS.keys())[:2]
        trade_locs = self._make_trade_locations(names)
        non_trade = Location(id="nt-1", name=names[0], location_type="system", has_trade_terminal=False)
        loc_svc = self._make_location_service(trade_locs + [non_trade])
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        # Still only pairs from the 2 trade locations
        assert len(result) == 2  # 1 pair × 2 travel types

    @pytest.mark.anyio
    async def test_locations_without_coords_are_skipped(self) -> None:
        """Locations whose name is absent from _LOCATION_COORDS are skipped."""
        trade_locs = [
            Location(id="loc-0", name="Port Olisar", location_type="station", has_trade_terminal=True),
            Location(id="loc-1", name="Unknown Station", location_type="station", has_trade_terminal=True),
        ]
        loc_svc = self._make_location_service(trade_locs)
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        assert result == []

    @pytest.mark.anyio
    async def test_all_created_records_have_ids(self) -> None:
        """Every returned LocationDistance has an id assigned."""
        names = list(_LOCATION_COORDS.keys())[:2]
        trade_locs = self._make_trade_locations(names)
        loc_svc = self._make_location_service(trade_locs)
        dist_svc = self._make_distance_service()

        result = await seed_distances(loc_svc, dist_svc)

        for record in result:
            assert record.id is not None

    def test_compute_distance_correctness(self) -> None:
        """compute_distance returns expected Euclidean distance."""
        a = (0.0, 0.0, 0.0)
        b = (3.0, 4.0, 0.0)
        assert math.isclose(compute_distance(a, b), 5.0)

    def test_location_coords_covers_all_seeded_locations(self) -> None:
        """Every location in _LOCATION_DEFS has an entry in _LOCATION_COORDS."""
        seeded_names = {d[0] for d in _LOCATION_DEFS}
        assert seeded_names <= set(_LOCATION_COORDS.keys())
