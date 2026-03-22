"""Unit tests for MongoLocationRepository.update()."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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

    @pytest.mark.anyio
    async def test_update_returns_location_with_id_on_match(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location()
        updated = await repo.update("507f1f77bcf86cd799439011", location)

        assert updated is not None
        assert updated.id == "507f1f77bcf86cd799439011"
        assert updated.name == "Port Olisar"
        collection.replace_one.assert_called_once()

    @pytest.mark.anyio
    async def test_update_returns_none_when_not_matched(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 0
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location()
        updated = await repo.update("507f1f77bcf86cd799439011", location)

        assert updated is None

    @pytest.mark.anyio
    async def test_update_does_not_mutate_input(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationRepository(collection)
        location = _make_location("different-id")
        original_id = location.id
        await repo.update("507f1f77bcf86cd799439011", location)

        assert location.id == original_id


class TestMongoLocationRepositoryFindAncestors:
    """Verify find_ancestors() iteratively follows parent_id chain, excluding system root."""

    def _make_repo(self) -> MongoLocationRepository:
        return MongoLocationRepository(AsyncMock())

    @pytest.mark.anyio
    async def test_returns_empty_list_for_nonexistent_location(self) -> None:
        repo = self._make_repo()
        repo.find_by_id = AsyncMock(return_value=None)
        result = await repo.find_ancestors("missing-id")
        assert result == []

    @pytest.mark.anyio
    async def test_returns_single_item_for_direct_child_of_system(self) -> None:
        system = Location(id="sys-1", name="Stanton", location_type="system", parent_id=None)
        planet = Location(id="planet-1", name="ArcCorp", location_type="planet", parent_id="sys-1")

        call_map = {"planet-1": planet, "sys-1": system}
        repo = self._make_repo()
        repo.find_by_id = AsyncMock(side_effect=lambda x: call_map.get(x))
        result = await repo.find_ancestors("planet-1")

        assert len(result) == 1
        assert result[0].id == "planet-1"

    @pytest.mark.anyio
    async def test_returns_chain_excluding_system(self) -> None:
        system = Location(id="sys-1", name="Stanton", location_type="system", parent_id=None)
        planet = Location(id="planet-1", name="ArcCorp", location_type="planet", parent_id="sys-1")
        city = Location(id="city-1", name="Area 18", location_type="city", parent_id="planet-1")

        call_map = {"city-1": city, "planet-1": planet, "sys-1": system}
        repo = self._make_repo()
        repo.find_by_id = AsyncMock(side_effect=lambda x: call_map.get(x))
        result = await repo.find_ancestors("city-1")

        assert len(result) == 2
        assert result[0].id == "city-1"
        assert result[1].id == "planet-1"

    @pytest.mark.anyio
    async def test_stops_when_parent_not_found(self) -> None:
        station = Location(id="sta-1", name="ARC-L1", location_type="station", parent_id="missing-parent")

        call_map = {"sta-1": station, "missing-parent": None}
        repo = self._make_repo()
        repo.find_by_id = AsyncMock(side_effect=lambda x: call_map.get(x))
        result = await repo.find_ancestors("sta-1")

        assert len(result) == 1
        assert result[0].id == "sta-1"


class TestUpsertByName:
    @pytest.mark.anyio
    async def test_inserts_new_location(self) -> None:
        from bson import ObjectId

        collection = AsyncMock()
        collection.find_one.return_value = None
        oid = ObjectId()
        collection.find_one_and_update.return_value = {
            "_id": oid,
            "name": "Hurston",
            "location_type": "planet",
            "in_game": True,
        }

        repo = MongoLocationRepository(collection)
        entity, changed = await repo.upsert_by_name(
            Location(name="Hurston", location_type="planet"),
        )

        assert changed is True
        assert entity.name == "Hurston"
        collection.find_one_and_update.assert_called_once()

    @pytest.mark.anyio
    async def test_skips_when_no_key_changes(self) -> None:
        from bson import ObjectId

        oid = ObjectId()
        collection = AsyncMock()
        collection.find_one.return_value = {
            "_id": oid,
            "name": "Hurston",
            "location_type": "planet",
            "in_game": True,
        }

        repo = MongoLocationRepository(collection)
        entity, changed = await repo.upsert_by_name(
            Location(name="Hurston", location_type="planet"),
        )

        assert changed is False
        assert entity.name == "Hurston"

    @pytest.mark.anyio
    async def test_updates_when_key_field_changed(self) -> None:
        from bson import ObjectId

        oid = ObjectId()
        existing = {
            "_id": oid,
            "name": "Hurston",
            "location_type": "planet",
            "in_game": True,
        }
        collection = AsyncMock()
        collection.find_one.return_value = existing
        collection.find_one_and_update.return_value = {
            "_id": oid,
            "name": "Hurston",
            "location_type": "moon",
            "in_game": True,
        }

        repo = MongoLocationRepository(collection)
        entity, changed = await repo.upsert_by_name(
            Location(name="Hurston", location_type="moon"),
        )

        assert changed is True
        collection.find_one_and_update.assert_called_once()
