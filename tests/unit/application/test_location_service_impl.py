"""Unit tests for LocationServiceImpl.update()."""

from unittest.mock import AsyncMock

import pytest

from src.application.services.location_service_impl import LocationServiceImpl
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Location


class TestLocationServiceImplUpdate:
    """Verify update() delegates to repository and raises on missing."""

    @staticmethod
    def _make_location(location_id: str = "loc-1") -> Location:
        return Location(
            id=location_id,
            name="Port Olisar",
            location_type="station",
            parent_id="sys-1",
            has_trade_terminal=True,
            has_landing_pad=True,
            landing_pad_size="large",
        )

    @pytest.mark.anyio
    async def test_update_returns_updated_location(self) -> None:
        repo = AsyncMock()
        existing = self._make_location()
        updated = self._make_location()
        updated.name = "Port Olisar Updated"
        repo.find_by_id.return_value = existing
        repo.update.return_value = updated

        service = LocationServiceImpl(repo)
        result = await service.update("loc-1", updated)

        assert result.name == "Port Olisar Updated"
        repo.find_by_id.assert_called_once_with("loc-1")
        repo.update.assert_called_once_with("loc-1", updated)

    @pytest.mark.anyio
    async def test_update_raises_when_not_found(self) -> None:
        repo = AsyncMock()
        repo.find_by_id.return_value = None

        service = LocationServiceImpl(repo)
        with pytest.raises(LocationNotFoundError):
            await service.update("missing-id", self._make_location())

        repo.update.assert_not_called()

    @pytest.mark.anyio
    async def test_update_raises_when_repo_update_returns_none(self) -> None:
        repo = AsyncMock()
        existing = self._make_location()
        repo.find_by_id.return_value = existing
        repo.update.return_value = None

        service = LocationServiceImpl(repo)
        with pytest.raises(LocationNotFoundError):
            await service.update("loc-1", self._make_location())


class TestLocationServiceImplGetAncestors:
    """Verify get_ancestors() delegates to repository and raises on missing location."""

    @staticmethod
    def _make_location(
        location_id: str = "loc-1", location_type: str = "city", parent_id: str | None = "planet-1"
    ) -> Location:
        return Location(
            id=location_id,
            name="Area 18",
            location_type=location_type,
            parent_id=parent_id,
        )

    @pytest.mark.anyio
    async def test_raises_when_location_not_found(self) -> None:
        repo = AsyncMock()
        repo.find_by_id.return_value = None

        service = LocationServiceImpl(repo)
        with pytest.raises(LocationNotFoundError):
            await service.get_ancestors("missing-id")

        repo.find_ancestors.assert_not_called()

    @pytest.mark.anyio
    async def test_returns_ancestor_chain_from_repository(self) -> None:
        repo = AsyncMock()
        city = self._make_location("city-1", "city", "planet-1")
        planet = self._make_location("planet-1", "planet", None)
        repo.find_by_id.return_value = city
        repo.find_ancestors.return_value = [city, planet]

        service = LocationServiceImpl(repo)
        result = await service.get_ancestors("city-1")

        assert len(result) == 2
        assert result[0].id == "city-1"
        assert result[1].id == "planet-1"
        repo.find_ancestors.assert_called_once_with("city-1")

    @pytest.mark.anyio
    async def test_caches_result_on_second_call(self) -> None:
        repo = AsyncMock()
        city = self._make_location("city-1")
        repo.find_by_id.return_value = city
        repo.find_ancestors.return_value = [city]

        service = LocationServiceImpl(repo)
        await service.get_ancestors("city-1")
        await service.get_ancestors("city-1")

        assert repo.find_ancestors.call_count == 1
