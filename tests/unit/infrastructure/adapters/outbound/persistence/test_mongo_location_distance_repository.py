"""Unit tests for MongoLocationDistanceRepository."""

from unittest.mock import MagicMock

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
    def test_save_new_inserts_and_returns_with_id(self) -> None:
        collection = MagicMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="aaa", to_location_id="bbb", distance=100.0, travel_type="quantum")
        result = repo.save(distance)

        collection.insert_one.assert_called_once()
        assert result.id == _OID

    def test_save_existing_calls_replace_one(self) -> None:
        collection = MagicMock()

        repo = MongoLocationDistanceRepository(collection)
        result = repo.save(_make_distance())

        collection.replace_one.assert_called_once()
        assert result is not None

    def test_save_normalizes_pair(self) -> None:
        collection = MagicMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="zzz", to_location_id="aaa", distance=50.0, travel_type="scm")
        result = repo.save(distance)

        # After normalization from < to alphabetically
        assert result.from_location_id == "aaa"
        assert result.to_location_id == "zzz"

    def test_save_does_not_mutate_input(self) -> None:
        collection = MagicMock()
        collection.insert_one.return_value = MagicMock(inserted_id=ObjectId(_OID))

        repo = MongoLocationDistanceRepository(collection)
        distance = LocationDistance(from_location_id="zzz", to_location_id="aaa", distance=50.0, travel_type="scm")
        repo.save(distance)

        assert distance.from_location_id == "zzz"
        assert distance.to_location_id == "aaa"


class TestMongoLocationDistanceRepositoryFindById:
    def test_find_by_id_returns_distance_when_found(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        result = repo.find_by_id(_OID)

        assert result is not None
        assert result.id == _OID
        assert result.from_location_id == "aaa"

    def test_find_by_id_returns_none_when_not_found(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        result = repo.find_by_id(_OID)

        assert result is None


class TestMongoLocationDistanceRepositoryFindByLocation:
    def test_find_by_location_returns_list(self) -> None:
        collection = MagicMock()
        collection.find.return_value = [_make_doc()]

        repo = MongoLocationDistanceRepository(collection)
        results = repo.find_by_location("aaa")

        assert len(results) == 1
        assert results[0].from_location_id == "aaa"

    def test_find_by_location_uses_or_query(self) -> None:
        collection = MagicMock()
        collection.find.return_value = []

        repo = MongoLocationDistanceRepository(collection)
        repo.find_by_location("loc-1")

        call_args = collection.find.call_args[0][0]
        assert "$or" in call_args
        conditions = call_args["$or"]
        assert {"from_location_id": "loc-1"} in conditions
        assert {"to_location_id": "loc-1"} in conditions


class TestMongoLocationDistanceRepositoryFindByPair:
    def test_find_by_pair_returns_distance_when_found(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = _make_doc()

        repo = MongoLocationDistanceRepository(collection)
        result = repo.find_by_pair("aaa", "bbb")

        assert result is not None
        assert result.id == _OID

    def test_find_by_pair_normalizes_argument_order(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        repo.find_by_pair("zzz", "aaa")

        call_args = collection.find_one.call_args[0][0]
        assert call_args["from_location_id"] == "aaa"
        assert call_args["to_location_id"] == "zzz"

    def test_find_by_pair_returns_none_when_not_found(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = None

        repo = MongoLocationDistanceRepository(collection)
        result = repo.find_by_pair("aaa", "bbb")

        assert result is None


class TestMongoLocationDistanceRepositoryUpdate:
    def test_update_returns_distance_with_id_on_match(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        updated = repo.update(_OID, _make_distance())

        assert updated is not None
        assert updated.id == _OID
        collection.replace_one.assert_called_once()

    def test_update_returns_none_when_not_matched(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 0
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        updated = repo.update(_OID, _make_distance())

        assert updated is None

    def test_update_does_not_mutate_input(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.matched_count = 1
        collection.replace_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        distance = _make_distance("different-id")
        original_id = distance.id
        repo.update(_OID, distance)

        assert distance.id == original_id


class TestMongoLocationDistanceRepositoryDelete:
    def test_delete_returns_true_when_deleted(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.deleted_count = 1
        collection.delete_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        assert repo.delete(_OID) is True

    def test_delete_returns_false_when_not_found(self) -> None:
        collection = MagicMock()
        result_mock = MagicMock()
        result_mock.deleted_count = 0
        collection.delete_one.return_value = result_mock

        repo = MongoLocationDistanceRepository(collection)
        assert repo.delete(_OID) is False


class TestMongoLocationDistanceRepositoryFindByTravelType:
    def test_find_by_travel_type_returns_matching_list(self) -> None:
        collection = MagicMock()
        wormhole_doc = {**_make_doc(), "travel_type": "wormhole"}
        collection.find.return_value = [wormhole_doc]

        repo = MongoLocationDistanceRepository(collection)
        results = repo.find_by_travel_type("wormhole")

        assert len(results) == 1
        assert results[0].travel_type == "wormhole"

    def test_find_by_travel_type_queries_correct_field(self) -> None:
        collection = MagicMock()
        collection.find.return_value = []

        repo = MongoLocationDistanceRepository(collection)
        repo.find_by_travel_type("wormhole")

        call_args = collection.find.call_args[0][0]
        assert call_args == {"travel_type": "wormhole"}

    def test_find_by_travel_type_returns_empty_list_when_none(self) -> None:
        collection = MagicMock()
        collection.find.return_value = []

        repo = MongoLocationDistanceRepository(collection)
        results = repo.find_by_travel_type("on_foot")

        assert results == []
