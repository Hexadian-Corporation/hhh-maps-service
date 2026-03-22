"""Unit tests for MongoLocationDistanceRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from src.domain.models.location_distance import LocationDistance
from src.infrastructure.adapters.outbound.persistence.mongo_location_distance_repository import (
    MongoLocationDistanceRepository,
)

_OID = "507f1f77bcf86cd799439011"
_OID2 = "507f1f77bcf86cd799439012"


def _make_distance(distance_id: str | None = _OID) -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id="aaa",
        to_location_id="bbb",
        distance=1500.0,
        travel_type="quantum",
    )


def _make_doc(distance_id: str = _OID) -> dict:
    return {
        "_id": ObjectId(distance_id),
        "from_location_id": "aaa",
        "to_location_id": "bbb",
        "distance": 1500.0,
        "travel_type": "quantum",
        "in_game": True,
    }


class TestMongoLocationDistanceRepositorySave:
    @pytest.mark.anyio
    async def test_save_new_inserts_and_returns_with_id(self) -> None:
        collection = AsyncMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="aaa", to_location_id="bbb", distance=100.0, travel_type="quantum")
        result = await repo.save(distance)

        collection.insert_one.assert_called_once()
        assert result.id == _OID

    @pytest.mark.anyio
    async def test_save_existing_calls_replace_one(self) -> None:
        collection = AsyncMock()

        repo = MongoLocationDistanceRepository(collection)
        result = await repo.save(_make_distance())

        collection.replace_one.assert_called_once()
        assert result is not None

    @pytest.mark.anyio
    async def test_save_normalizes_pair(self) -> None:
        collection = AsyncMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="zzz", to_location_id="aaa", distance=50.0, travel_type="scm")
        result = await repo.save(distance)

        # After normalization from < to alphabetically
        assert result.from_location_id == "aaa"
        assert result.to_location_id == "zzz"

    @pytest.mark.anyio
    async def test_save_does_not_mutate_input(self) -> None:
        collection = AsyncMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="zzz", to_location_id="aaa", distance=50.0, travel_type="scm")
        await repo.save(distance)

        assert distance.from_location_id == "zzz"
        assert distance.to_location_id == "aaa"


class TestMongoLocationDistanceRepositoryFindById:
    @pytest.mark.anyio
    async def test_find_by_id_returns_distance_when_found(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        result = await repo.find_by_id(_OID)

        assert result is not None
        assert result.id == _OID
        assert result.from_location_id == "aaa"

    @pytest.mark.anyio
    async def test_find_by_id_returns_none_when_not_found(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        result = await repo.find_by_id(_OID)

        assert result is None


class TestMongoLocationDistanceRepositoryFindByLocation:
    @pytest.mark.anyio
    async def test_find_by_location_returns_list(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        collection.find.return_value.to_list = AsyncMock(return_value=[_make_doc()])

        repo = MongoLocationDistanceRepository(collection)
        results = await repo.find_by_location("aaa")

        assert len(results) == 1
        assert results[0].from_location_id == "aaa"

    @pytest.mark.anyio
    async def test_find_by_location_uses_or_query(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        collection.find.return_value.to_list = AsyncMock(return_value=[])

        repo = MongoLocationDistanceRepository(collection)
        await repo.find_by_location("loc-1")

        call_args = collection.find.call_args[0][0]
        assert "$or" in call_args
        conditions = call_args["$or"]
        assert {"from_location_id": "loc-1"} in conditions
        assert {"to_location_id": "loc-1"} in conditions


class TestMongoLocationDistanceRepositoryFindByPair:
    @pytest.mark.anyio
    async def test_find_by_pair_returns_distance_when_found(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        result = await repo.find_by_pair("aaa", "bbb")

        assert result is not None
        assert result.id == _OID

    @pytest.mark.anyio
    async def test_find_by_pair_normalizes_argument_order(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        await repo.find_by_pair("zzz", "aaa")

        call_args = collection.find_one.call_args[0][0]
        assert call_args["from_location_id"] == "aaa"
        assert call_args["to_location_id"] == "zzz"

    @pytest.mark.anyio
    async def test_find_by_pair_returns_none_when_not_found(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        result = await repo.find_by_pair("aaa", "bbb")

        assert result is None


class TestMongoLocationDistanceRepositoryUpdate:
    @pytest.mark.anyio
    async def test_update_returns_distance_with_id_on_match(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        updated = await repo.update(_OID, _make_distance())

        assert updated is not None
        assert updated.id == _OID
        collection.replace_one.assert_called_once()

    @pytest.mark.anyio
    async def test_update_returns_none_when_not_matched(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 0
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        updated = await repo.update(_OID, _make_distance())

        assert updated is None

    @pytest.mark.anyio
    async def test_update_does_not_mutate_input(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        distance = _make_distance("different-id")
        original_id = distance.id
        await repo.update(_OID, distance)

        assert distance.id == original_id


class TestMongoLocationDistanceRepositoryDelete:
    @pytest.mark.anyio
    async def test_delete_returns_true_when_deleted(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.deleted_count = 1
        collection.delete_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        assert await repo.delete(_OID) is True

    @pytest.mark.anyio
    async def test_delete_returns_false_when_not_found(self) -> None:
        collection = AsyncMock()
        result_mock = MagicMock()
        result_mock.deleted_count = 0
        collection.delete_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        assert await repo.delete(_OID) is False


class TestMongoLocationDistanceRepositoryFindByTravelType:
    @pytest.mark.anyio
    async def test_find_by_travel_type_returns_matching_list(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        wormhole_doc = {**_make_doc(), "travel_type": "wormhole"}
        collection.find.return_value.to_list = AsyncMock(return_value=[wormhole_doc])

        repo = MongoLocationDistanceRepository(collection)
        results = await repo.find_by_travel_type("wormhole")

        assert len(results) == 1
        assert results[0].travel_type == "wormhole"

    @pytest.mark.anyio
    async def test_find_by_travel_type_queries_correct_field(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        collection.find.return_value.to_list = AsyncMock(return_value=[])

        repo = MongoLocationDistanceRepository(collection)
        await repo.find_by_travel_type("wormhole")

        call_args = collection.find.call_args[0][0]
        assert call_args == {"travel_type": "wormhole"}

    @pytest.mark.anyio
    async def test_find_by_travel_type_returns_empty_list_when_none(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        collection.find.return_value.to_list = AsyncMock(return_value=[])

        repo = MongoLocationDistanceRepository(collection)
        results = await repo.find_by_travel_type("on_foot")

        assert results == []


class TestUpsertByPair:
    @pytest.mark.anyio
    async def test_inserts_new_distance(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = None
        collection.find_one_and_update.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        entity, changed = await repo.upsert_by_pair(_make_distance(None))

        assert changed is True
        assert entity.distance == 1500.0
        collection.find_one_and_update.assert_called_once()

    @pytest.mark.anyio
    async def test_skips_when_no_key_changes(self) -> None:
        collection = AsyncMock()
        collection.find_one.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        entity, changed = await repo.upsert_by_pair(_make_distance(None))

        assert changed is False
        assert entity.distance == 1500.0

    @pytest.mark.anyio
    async def test_updates_when_distance_changed(self) -> None:
        existing = _make_doc()
        collection = AsyncMock()
        collection.find_one.return_value = existing
        updated = dict(existing)
        updated["distance"] = 2000.0
        collection.find_one_and_update.return_value = updated

        repo = MongoLocationDistanceRepository(collection)
        distance = _make_distance(None)
        distance.distance = 2000.0
        entity, changed = await repo.upsert_by_pair(distance)

        assert changed is True
        assert entity.distance == 2000.0
        collection.find_one_and_update.assert_called_once()
