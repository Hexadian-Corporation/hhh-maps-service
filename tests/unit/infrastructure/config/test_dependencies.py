"""Unit tests for AppModule – verify MongoDB indexes are created on startup."""

from unittest.mock import MagicMock, call, patch

from pymongo.collation import Collation

from src.infrastructure.config.settings import Settings


class TestAppModuleIndexes:
    """Verify create_index is called for location_type, parent_id, and name."""

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_indexes_created_on_configure(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_locations_collection = MagicMock()
        mock_distance_collection = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: (
            mock_locations_collection if name == "locations" else mock_distance_collection
        )

        settings = Settings(mongo_uri="mongodb://localhost:27017", mongo_db="test_db")

        from src.infrastructure.config.dependencies import AppModule

        module = AppModule(settings)
        module.configure()

        location_calls = mock_locations_collection.create_index.call_args_list
        assert len(location_calls) == 3
        assert location_calls[0].args == ("location_type",)
        assert location_calls[1].args == ("parent_id",)
        assert location_calls[2].args == ("name",)
        collation_kwarg = location_calls[2].kwargs["collation"]
        assert isinstance(collation_kwarg, Collation)

        distance_calls = mock_distance_collection.create_index.call_args_list
        assert len(distance_calls) == 3
        assert distance_calls[0] == call(
            [("from_location_id", 1), ("to_location_id", 1)],
            unique=True,
        )
        assert distance_calls[1] == call("from_location_id")
        assert distance_calls[2] == call("to_location_id")
