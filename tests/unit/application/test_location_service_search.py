"""Unit tests for LocationServiceImpl.search_by_name."""

from unittest.mock import AsyncMock

import pytest

from src.application.services.location_service_impl import LocationServiceImpl
from src.domain.models.location import Location


class TestSearchByName:
    """Verify search_by_name delegates to repository and handles empty query."""

    @staticmethod
    def _make_service(repository: AsyncMock | None = None) -> tuple[LocationServiceImpl, AsyncMock]:
        repo = repository or AsyncMock()
        return LocationServiceImpl(repo), repo

    @pytest.mark.anyio
    async def test_delegates_to_repository(self) -> None:
        service, repo = self._make_service()
        expected = [Location(id="1", name="Lorville")]
        repo.search_by_name.return_value = expected

        result = await service.search_by_name("lor")

        repo.search_by_name.assert_called_once_with("lor")
        assert result == expected

    @pytest.mark.anyio
    async def test_returns_empty_list_for_empty_query(self) -> None:
        service, repo = self._make_service()

        result = await service.search_by_name("")

        assert result == []
        repo.search_by_name.assert_not_called()

    @pytest.mark.anyio
    async def test_returns_multiple_matches(self) -> None:
        service, repo = self._make_service()
        expected = [
            Location(id="1", name="Port Olisar"),
            Location(id="2", name="Port Tressler"),
        ]
        repo.search_by_name.return_value = expected

        result = await service.search_by_name("port")

        assert len(result) == 2
        assert result == expected
