"""Unit tests for MongoLocationRepository.search_by_name."""

from unittest.mock import MagicMock

from bson import ObjectId

from src.infrastructure.adapters.outbound.persistence.mongo_location_repository import MongoLocationRepository


class TestSearchByName:
    """Verify search_by_name uses correct MongoDB regex query."""

    @staticmethod
    def _make_repo() -> tuple[MongoLocationRepository, MagicMock]:
        collection = MagicMock()
        return MongoLocationRepository(collection), collection

    def test_queries_with_case_insensitive_regex(self) -> None:
        repo, collection = self._make_repo()
        collection.find.return_value = []

        repo.search_by_name("lor")

        collection.find.assert_called_once_with({"name": {"$regex": "lor", "$options": "i"}})

    def test_returns_mapped_domain_objects(self) -> None:
        repo, collection = self._make_repo()
        oid = ObjectId()
        collection.find.return_value = [
            {
                "_id": oid,
                "name": "Lorville",
                "location_type": "city",
                "parent_id": "p1",
                "coordinates": {"x": 1.0, "y": 2.0, "z": 3.0},
                "has_trade_terminal": True,
                "has_landing_pad": True,
                "landing_pad_size": "large",
            }
        ]

        result = repo.search_by_name("lor")

        assert len(result) == 1
        assert result[0].name == "Lorville"
        assert result[0].id == str(oid)
        assert result[0].location_type == "city"

    def test_returns_empty_list_when_no_matches(self) -> None:
        repo, collection = self._make_repo()
        collection.find.return_value = []

        result = repo.search_by_name("nonexistent")

        assert result == []

    def test_returns_multiple_results(self) -> None:
        repo, collection = self._make_repo()
        oid1 = ObjectId()
        oid2 = ObjectId()
        collection.find.return_value = [
            {"_id": oid1, "name": "Port Olisar", "location_type": "station", "coordinates": {}},
            {"_id": oid2, "name": "Port Tressler", "location_type": "station", "coordinates": {}},
        ]

        result = repo.search_by_name("port")

        assert len(result) == 2
        assert result[0].name == "Port Olisar"
        assert result[1].name == "Port Tressler"


class TestFindChildren:
    """Verify find_children queries with correct parent_id filter."""

    def test_returns_children_for_parent_id(self) -> None:
        collection = MagicMock()
        oid = ObjectId()
        collection.find.return_value = [
            {
                "_id": oid,
                "name": "Lorville",
                "location_type": "city",
                "parent_id": "parent1",
                "coordinates": {"x": 1.0, "y": 2.0, "z": 3.0},
            }
        ]
        repo = MongoLocationRepository(collection)

        result = repo.find_children("parent1")

        collection.find.assert_called_once_with({"parent_id": "parent1"})
        assert len(result) == 1
        assert result[0].name == "Lorville"
