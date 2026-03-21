"""Unit tests for LocationServiceImpl TTL cache behavior."""

from unittest.mock import AsyncMock

import pytest

from src.application.services.location_service_impl import LocationServiceImpl
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Location


def _make_location(location_id: str = "loc-1", name: str = "Port Olisar") -> Location:
    return Location(
        id=location_id,
        name=name,
        location_type="station",
        parent_id="sys-1",
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


def _make_service(repo: AsyncMock | None = None) -> tuple[LocationServiceImpl, AsyncMock]:
    repo = repo or AsyncMock()
    return LocationServiceImpl(repo), repo


class TestCacheHit:
    """Verify second call within TTL returns cached result (repo not called again)."""

    @pytest.mark.anyio
    async def test_list_all_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]

        await service.list_all()
        await service.list_all()

        assert repo.find_all.call_count == 1

    @pytest.mark.anyio
    async def test_list_by_type_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_type.return_value = [_make_location()]

        await service.list_by_type("station")
        await service.list_by_type("station")

        assert repo.find_by_type.call_count == 1

    @pytest.mark.anyio
    async def test_list_by_type_different_types_not_cached(self) -> None:
        service, repo = _make_service()
        repo.find_by_type.return_value = []

        await service.list_by_type("station")
        await service.list_by_type("city")

        assert repo.find_by_type.call_count == 2

    @pytest.mark.anyio
    async def test_list_children_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_children.return_value = [_make_location()]

        await service.list_children("sys-1")
        await service.list_children("sys-1")

        assert repo.find_children.call_count == 1

    @pytest.mark.anyio
    async def test_search_by_name_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.search_by_name.return_value = [_make_location()]

        await service.search_by_name("port")
        await service.search_by_name("port")

        assert repo.search_by_name.call_count == 1

    @pytest.mark.anyio
    async def test_search_by_name_different_queries_not_cached(self) -> None:
        service, repo = _make_service()
        repo.search_by_name.return_value = []

        await service.search_by_name("port")
        await service.search_by_name("lor")

        assert repo.search_by_name.call_count == 2


class TestCacheInvalidation:
    """Verify CUD operations invalidate cache."""

    @pytest.mark.anyio
    async def test_create_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.save.return_value = _make_location("new-1")

        await service.list_all()
        await service.create(_make_location(location_id=None))
        await service.list_all()

        assert repo.find_all.call_count == 2

    @pytest.mark.anyio
    async def test_update_invalidates_cache(self) -> None:
        service, repo = _make_service()
        existing = _make_location()
        repo.find_all.return_value = [existing]
        repo.find_by_id.return_value = existing
        repo.update.return_value = existing

        await service.list_all()
        await service.update("loc-1", existing)
        await service.list_all()

        assert repo.find_all.call_count == 2

    @pytest.mark.anyio
    async def test_delete_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.delete.return_value = True

        await service.list_all()
        await service.delete("loc-1")
        await service.list_all()

        assert repo.find_all.call_count == 2

    @pytest.mark.anyio
    async def test_failed_delete_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.delete.return_value = False

        await service.list_all()
        with pytest.raises(LocationNotFoundError):
            await service.delete("missing")
        await service.list_all()

        assert repo.find_all.call_count == 1

    @pytest.mark.anyio
    async def test_failed_update_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.find_by_id.return_value = None

        await service.list_all()
        with pytest.raises(LocationNotFoundError):
            await service.update("missing", _make_location())
        await service.list_all()

        assert repo.find_all.call_count == 1
