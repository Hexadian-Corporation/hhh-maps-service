"""Tests for LocationImportHandler and DistanceImportHandler."""

from unittest.mock import AsyncMock

import pytest
from hhh_events import EventDocument, EventMode

from src.application.services.import_handler import DistanceImportHandler, LocationImportHandler
from src.domain.models.location import Location
from src.domain.models.location_distance import LocationDistance


@pytest.fixture
def mock_location_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.upsert_by_name.return_value = (Location(id="1", name="Stanton"), True)
    return repo


@pytest.fixture
def mock_distance_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.upsert_by_pair.return_value = (LocationDistance(id="d1"), True)
    return repo


@pytest.fixture
def mock_publisher() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def location_handler(mock_location_repo: AsyncMock, mock_publisher: AsyncMock) -> LocationImportHandler:
    return LocationImportHandler(repository=mock_location_repo, publisher=mock_publisher)


@pytest.fixture
def distance_handler(
    mock_distance_repo: AsyncMock, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
) -> DistanceImportHandler:
    return DistanceImportHandler(
        distance_repository=mock_distance_repo,
        location_repository=mock_location_repo,
        publisher=mock_publisher,
    )


class TestLocationImportHandler:
    @pytest.mark.anyio
    async def test_handle_upserts_locations(
        self, location_handler: LocationImportHandler, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        event = EventDocument(
            type="locations.bulk_import",
            source_service="dataminer",
            modified_ids=["uex:location:Stanton", "uex:location:Hurston"],
            mode=EventMode.FULL_SYNC,
            metadata={
                "items": [
                    {"id": "uex:location:Stanton", "name": "Stanton", "type": "system"},
                    {"id": "uex:location:Hurston", "name": "Hurston", "type": "planet"},
                ]
            },
        )

        count = await location_handler.handle(event)

        assert count == 2
        assert mock_location_repo.upsert_by_name.call_count == 2
        mock_publisher.publish.assert_called_once()
        published = mock_publisher.publish.call_args.args[0]
        assert published.type == "locations.imported"
        assert published.modified_ids == ["1", "1"]

    @pytest.mark.anyio
    async def test_handle_skips_items_without_name(
        self, location_handler: LocationImportHandler, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        event = EventDocument(
            type="locations.bulk_import",
            source_service="dataminer",
            modified_ids=["uex:location:1"],
            mode=EventMode.FULL_SYNC,
            metadata={"items": [{"id": "uex:location:1", "name": "", "type": "system"}]},
        )

        count = await location_handler.handle(event)

        assert count == 0
        mock_location_repo.upsert_by_name.assert_not_called()
        mock_publisher.publish.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_skips_unchanged(
        self, location_handler: LocationImportHandler, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        mock_location_repo.upsert_by_name.return_value = (
            Location(id="1", name="Stanton"), False,
        )
        event = EventDocument(
            type="locations.bulk_import",
            source_service="dataminer",
            modified_ids=["uex:location:Stanton"],
            mode=EventMode.FULL_SYNC,
            metadata={"items": [{"id": "uex:location:Stanton", "name": "Stanton", "type": "system"}]},
        )

        count = await location_handler.handle(event)

        assert count == 0
        mock_location_repo.upsert_by_name.assert_called_once()
        mock_publisher.publish.assert_not_called()


class TestDistanceImportHandler:
    @pytest.mark.anyio
    async def test_handle_upserts_distances(
        self, distance_handler: DistanceImportHandler,
        mock_distance_repo: AsyncMock, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        mock_location_repo.search_by_name.side_effect = [
            [Location(id="abc", name="Hurston")],
            [Location(id="def", name="ArcCorp")],
        ]

        event = EventDocument(
            type="distances.bulk_import",
            source_service="dataminer",
            modified_ids=[],
            mode=EventMode.FULL_SYNC,
            metadata={
                "items": [
                    {"from_id": "uex:location:Hurston", "to_id": "uex:location:ArcCorp", "distance": 1000000},
                ]
            },
        )

        count = await distance_handler.handle(event)

        assert count == 1
        mock_distance_repo.upsert_by_pair.assert_called_once()
        distance = mock_distance_repo.upsert_by_pair.call_args.args[0]
        assert distance.from_location_id == "abc"
        assert distance.to_location_id == "def"
        mock_publisher.publish.assert_called_once()
        published = mock_publisher.publish.call_args.args[0]
        assert published.type == "distances.imported"
        assert published.modified_ids == ["d1"]

    @pytest.mark.anyio
    async def test_handle_skips_unresolved_locations(
        self, distance_handler: DistanceImportHandler,
        mock_distance_repo: AsyncMock, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        mock_location_repo.search_by_name.return_value = []

        event = EventDocument(
            type="distances.bulk_import",
            source_service="dataminer",
            modified_ids=[],
            mode=EventMode.FULL_SYNC,
            metadata={
                "items": [
                    {"from_id": "uex:location:Unknown1", "to_id": "uex:location:Unknown2", "distance": 500},
                ]
            },
        )

        count = await distance_handler.handle(event)

        assert count == 0
        mock_distance_repo.upsert_by_pair.assert_not_called()
        mock_publisher.publish.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_skips_unchanged(
        self, distance_handler: DistanceImportHandler,
        mock_distance_repo: AsyncMock, mock_location_repo: AsyncMock, mock_publisher: AsyncMock,
    ) -> None:
        mock_location_repo.search_by_name.side_effect = [
            [Location(id="abc", name="Hurston")],
            [Location(id="def", name="ArcCorp")],
        ]
        mock_distance_repo.upsert_by_pair.return_value = (LocationDistance(id="d1"), False)

        event = EventDocument(
            type="distances.bulk_import",
            source_service="dataminer",
            modified_ids=[],
            mode=EventMode.FULL_SYNC,
            metadata={
                "items": [
                    {"from_id": "uex:location:Hurston", "to_id": "uex:location:ArcCorp", "distance": 1000000},
                ]
            },
        )

        count = await distance_handler.handle(event)

        assert count == 0
        mock_distance_repo.upsert_by_pair.assert_called_once()
        mock_publisher.publish.assert_not_called()
