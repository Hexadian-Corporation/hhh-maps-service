"""Unit tests for MongoLocationRepository.update()."""

from unittest.mock import MagicMock

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
