"""Unit tests for AppModule – verify MongoDB indexes are created on startup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.collation import Collation

from src.infrastructure.config.settings import Settings


class TestAppModuleIndexes:
    """Verify create_indexes() creates the expected indexes on location and distance collections."""

    @pytest.mark.anyio
    async def test_indexes_created_on_create_indexes(self) -> None:
        mock_location_collection = AsyncMock()
        mock_distance_collection = AsyncMock()
        mock_distance_collection.index_information.return_value = {}

        mock_db = MagicMock()
        mock_db.__getitem__.side_effect = lambda name: (
            mock_location_collection if name == "locations" else mock_distance_collection
        )

        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        settings = Settings(mongo_uri="mongodb://localhost:27017", mongo_db="test_db")

        with patch("src.infrastructure.config.dependencies.AsyncIOMotorClient", return_value=mock_client):
            from src.infrastructure.config.dependencies import AppModule

            module = AppModule(settings)
            await module.create_indexes()

        location_calls = mock_location_collection.create_index.call_args_list
        assert len(location_calls) == 3
        assert location_calls[0].args == ("location_type",)
        assert location_calls[1].args == ("parent_id",)
        assert location_calls[2].args == ("name",)
        collation_kwarg = location_calls[2].kwargs["collation"]
        assert isinstance(collation_kwarg, Collation)

        distance_calls = mock_distance_collection.create_index.call_args_list
        assert len(distance_calls) == 3
        first_distance_call = distance_calls[0]
        assert first_distance_call.args == ([("from_location_id", 1), ("to_location_id", 1), ("travel_type", 1)],)
        assert first_distance_call.kwargs.get("unique") is True
        assert distance_calls[1].args == ("from_location_id",)
        assert distance_calls[2].args == ("to_location_id",)
