"""Unit tests for AppModule – verify MongoDB indexes are created on startup."""

from unittest.mock import MagicMock, patch

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
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection

        settings = Settings(mongo_uri="mongodb://localhost:27017", mongo_db="test_db")

        from src.infrastructure.config.dependencies import AppModule

        module = AppModule(settings)
        module.configure()

        calls = mock_collection.create_index.call_args_list
        assert len(calls) == 3

        assert calls[0].args == ("location_type",)
        assert calls[1].args == ("parent_id",)
        assert calls[2].args == ("name",)
        collation_kwarg = calls[2].kwargs["collation"]
        assert isinstance(collation_kwarg, Collation)
