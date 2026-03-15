"""Unit tests for LocationServiceImpl.search_by_name and update."""

from unittest.mock import MagicMock

import pytest

from src.application.services.location_service_impl import LocationServiceImpl
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Coordinates, Location


class TestSearchByName:
    """Verify search_by_name delegates to repository and handles empty query."""

    @staticmethod
    def _make_service(repository: MagicMock | None = None) -> tuple[LocationServiceImpl, MagicMock]:
        repo = repository or MagicMock()
        return LocationServiceImpl(repo), repo

    def test_delegates_to_repository(self) -> None:
        service, repo = self._make_service()
        expected = [Location(id="1", name="Lorville")]
        repo.search_by_name.return_value = expected

        result = service.search_by_name("lor")

        repo.search_by_name.assert_called_once_with("lor")
        assert result == expected

    def test_returns_empty_list_for_empty_query(self) -> None:
        service, repo = self._make_service()

        result = service.search_by_name("")

        assert result == []
        repo.search_by_name.assert_not_called()

    def test_returns_multiple_matches(self) -> None:
        service, repo = self._make_service()
        expected = [
            Location(id="1", name="Port Olisar"),
            Location(id="2", name="Port Tressler"),
        ]
        repo.search_by_name.return_value = expected

        result = service.search_by_name("port")

        assert len(result) == 2
        assert result == expected


class TestLocationServiceImplUpdate:
    """Verify update() delegates to repository and raises on missing."""

    @staticmethod
    def _make_location(location_id: str = "loc-1") -> Location:
        return Location(
            id=location_id,
            name="Port Olisar",
            location_type="station",
            parent_id="sys-1",
            coordinates=Coordinates(x=1.0, y=2.0, z=3.0),
            has_trade_terminal=True,
            has_landing_pad=True,
            landing_pad_size="large",
        )

    def test_update_returns_updated_location(self) -> None:
        repo = MagicMock()
        existing = self._make_location()
        updated = self._make_location()
        updated.name = "Port Olisar Updated"
        repo.find_by_id.return_value = existing
        repo.update.return_value = updated

        service = LocationServiceImpl(repo)
        result = service.update("loc-1", updated)

        assert result.name == "Port Olisar Updated"
        repo.find_by_id.assert_called_once_with("loc-1")
        repo.update.assert_called_once_with("loc-1", updated)

    def test_update_raises_when_not_found(self) -> None:
        repo = MagicMock()
        repo.find_by_id.return_value = None

        service = LocationServiceImpl(repo)
        with pytest.raises(LocationNotFoundError):
            service.update("missing-id", self._make_location())

        repo.update.assert_not_called()

    def test_update_raises_when_repo_update_returns_none(self) -> None:
        repo = MagicMock()
        existing = self._make_location()
        repo.find_by_id.return_value = existing
        repo.update.return_value = None

        service = LocationServiceImpl(repo)
        with pytest.raises(LocationNotFoundError):
            service.update("loc-1", self._make_location())
