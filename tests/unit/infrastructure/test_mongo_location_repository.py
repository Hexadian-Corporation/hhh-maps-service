"""Unit tests for MongoLocationRepository.search_by_name."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from src.infrastructure.adapters.outbound.persistence.mongo_location_repository import MongoLocationRepository


class TestSearchByName:
    """Verify search_by_name uses correct MongoDB regex query."""

    @staticmethod
    def _make_repo() -> tuple[MongoLocationRepository, AsyncMock]:
        collection = AsyncMock()
        collection.find = MagicMock()
        return MongoLocationRepository(collection), collection

    @pytest.mark.anyio
    async def test_queries_with_case_insensitive_regex(self) -> None:
        repo, collection = self._make_repo()
        collection.find.return_value.to_list = AsyncMock(return_value=[])

        await repo.search_by_name("lor")

        collection.find.assert_called_once_with({"name": {"$regex": "lor", "$options": "i"}})

    @pytest.mark.anyio
    async def test_returns_mapped_domain_objects(self) -> None:
        repo, collection = self._make_repo()
        oid = ObjectId()
        collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {
                    "_id": oid,
                    "name": "Lorville",
                    "location_type": "city",
                    "parent_id": "p1",
                    "has_trade_terminal": True,
                    "has_landing_pad": True,
                    "landing_pad_size": "large",
                }
            ]
        )

        result = await repo.search_by_name("lor")

        assert len(result) == 1
        assert result[0].name == "Lorville"
        assert result[0].id == str(oid)
        assert result[0].location_type == "city"

    @pytest.mark.anyio
    async def test_returns_empty_list_when_no_matches(self) -> None:
        repo, collection = self._make_repo()
        collection.find.return_value.to_list = AsyncMock(return_value=[])

        result = await repo.search_by_name("nonexistent")

        assert result == []

    @pytest.mark.anyio
    async def test_returns_multiple_results(self) -> None:
        repo, collection = self._make_repo()
        oid1 = ObjectId()
        oid2 = ObjectId()
        collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {"_id": oid1, "name": "Port Olisar", "location_type": "station"},
                {"_id": oid2, "name": "Port Tressler", "location_type": "station"},
            ]
        )

        result = await repo.search_by_name("port")

        assert len(result) == 2
        assert result[0].name == "Port Olisar"
        assert result[1].name == "Port Tressler"


class TestFindChildren:
    """Verify find_children queries with correct parent_id filter."""

    @pytest.mark.anyio
    async def test_returns_children_for_parent_id(self) -> None:
        collection = AsyncMock()
        collection.find = MagicMock()
        oid = ObjectId()
        collection.find.return_value.to_list = AsyncMock(
            return_value=[
                {
                    "_id": oid,
                    "name": "Lorville",
                    "location_type": "city",
                    "parent_id": "parent1",
                }
            ]
        )
        repo = MongoLocationRepository(collection)

        result = await repo.find_children("parent1")

        collection.find.assert_called_once_with({"parent_id": "parent1"})
        assert len(result) == 1
        assert result[0].name == "Lorville"


class TestInvalidObjectId:
    """Verify repository methods handle invalid ObjectId strings gracefully."""

    @staticmethod
    def _make_repo() -> tuple[MongoLocationRepository, AsyncMock]:
        collection = AsyncMock()
        return MongoLocationRepository(collection), collection

    @pytest.mark.anyio
    async def test_save_with_invalid_id_returns_location_without_writing(self) -> None:
        repo, collection = self._make_repo()
        from src.domain.models.location import Location

        location = Location(id="not-valid", name="Ghost", location_type="planet")

        result = await repo.save(location)

        collection.replace_one.assert_not_called()
        collection.insert_one.assert_not_called()
        assert result is location

    @pytest.mark.anyio
    async def test_update_with_invalid_id_returns_none(self) -> None:
        repo, collection = self._make_repo()
        from src.domain.models.location import Location

        location = Location(name="Ghost", location_type="planet")

        result = await repo.update("not-valid", location)

        collection.replace_one.assert_not_called()
        assert result is None

    @pytest.mark.anyio
    async def test_delete_with_invalid_id_returns_false(self) -> None:
        repo, collection = self._make_repo()

        result = await repo.delete("not-valid")

        collection.delete_one.assert_not_called()
        assert result is False
