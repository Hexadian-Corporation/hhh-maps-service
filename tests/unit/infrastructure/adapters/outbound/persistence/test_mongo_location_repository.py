"""Unit tests for MongoLocationRepository.update()."""

from unittest.mock import MagicMock, patch

from src.domain.models.location import Location
from src.infrastructure.adapters.outbound.persistence.mongo_location_repository import MongoLocationRepository


def _make_location(location_id: str = "507f1f77bcf86cd799439011") -> Location:
    return Location(
        id=location_id,
        name="Port Olisar",
        location_type="station",
        parent_id="sys-1",
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


class TestMongoLocationRepositoryUpdate:
    """Verify update() calls replace_one and handles matched/unmatched."""

    def test_update_returns_location_with_id_on_match(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location()
        updated = repo.update("507f1f77bcf86cd799439011", location)

        assert updated is not None
        assert updated.id == "507f1f77bcf86cd799439011"
        assert updated.name == "Port Olisar"
        collection.replace_one.assert_called_once()

    def test_update_returns_none_when_not_matched(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 0
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location()
        updated = repo.update("507f1f77bcf86cd799439011", location)

        assert updated is None

    def test_update_does_not_mutate_input(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location("different-id")
        original_id = location.id
        repo.update("507f1f77bcf86cd799439011", location)

        assert location.id == original_id


class TestMongoLocationRepositoryFindAncestors:
    """Verify find_ancestors() iteratively follows parent_id chain, excluding system root."""

    def _make_repo(self) -> MongoLocationRepository:
        return MongoLocationRepository(MagicMock())

    def test_returns_empty_list_for_nonexistent_location(self) -> None:
        repo = self._make_repo()
        with patch.object(repo, "find_by_id", return_value=None):
            result = repo.find_ancestors("missing-id")
        assert result == []

    def test_returns_single_item_for_direct_child_of_system(self) -> None:
        system = Location(id="sys-1", name="Stanton", location_type="system", parent_id=None)
        planet = Location(id="planet-1", name="ArcCorp", location_type="planet", parent_id="sys-1")

        call_map = {"planet-1": planet, "sys-1": system}
        repo = self._make_repo()
        with patch.object(repo, "find_by_id", side_effect=lambda x: call_map.get(x)):
            result = repo.find_ancestors("planet-1")

        assert len(result) == 1
        assert result[0].id == "planet-1"

    def test_returns_chain_excluding_system(self) -> None:
        system = Location(id="sys-1", name="Stanton", location_type="system", parent_id=None)
        planet = Location(id="planet-1", name="ArcCorp", location_type="planet", parent_id="sys-1")
        city = Location(id="city-1", name="Area 18", location_type="city", parent_id="planet-1")

        call_map = {"city-1": city, "planet-1": planet, "sys-1": system}
        repo = self._make_repo()
        with patch.object(repo, "find_by_id", side_effect=lambda x: call_map.get(x)):
            result = repo.find_ancestors("city-1")

        assert len(result) == 2
        assert result[0].id == "city-1"
        assert result[1].id == "planet-1"

    def test_stops_when_parent_not_found(self) -> None:
        station = Location(id="sta-1", name="ARC-L1", location_type="station", parent_id="missing-parent")

        call_map = {"sta-1": station, "missing-parent": None}
        repo = self._make_repo()
        with patch.object(repo, "find_by_id", side_effect=lambda x: call_map.get(x)):
            result = repo.find_ancestors("sta-1")

        assert len(result) == 1
        assert result[0].id == "sta-1"
