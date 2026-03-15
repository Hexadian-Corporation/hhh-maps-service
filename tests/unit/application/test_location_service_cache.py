"""Unit tests for LocationServiceImpl TTL cache behavior."""

from unittest.mock import MagicMock

import pytest

from src.application.services.location_service_impl import LocationServiceImpl
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.domain.models.location import Coordinates, Location


def _make_location(location_id: str = "loc-1", name: str = "Port Olisar") -> Location:
    return Location(
        id=location_id,
        name=name,
        location_type="station",
        parent_id="sys-1",
        coordinates=Coordinates(x=1.0, y=2.0, z=3.0),
        has_trade_terminal=True,
        has_landing_pad=True,
        landing_pad_size="large",
    )


def _make_service(repo: MagicMock | None = None) -> tuple[LocationServiceImpl, MagicMock]:
    repo = repo or MagicMock()
    return LocationServiceImpl(repo), repo


class TestCacheHit:
    """Verify second call within TTL returns cached result (repo not called again)."""

    def test_list_all_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]

        service.list_all()
        service.list_all()

        assert repo.find_all.call_count == 1

    def test_list_by_type_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_type.return_value = [_make_location()]

        service.list_by_type("station")
        service.list_by_type("station")

        assert repo.find_by_type.call_count == 1

    def test_list_by_type_different_types_not_cached(self) -> None:
        service, repo = _make_service()
        repo.find_by_type.return_value = []

        service.list_by_type("station")
        service.list_by_type("city")

        assert repo.find_by_type.call_count == 2

    def test_list_children_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_children.return_value = [_make_location()]

        service.list_children("sys-1")
        service.list_children("sys-1")

        assert repo.find_children.call_count == 1

    def test_search_by_name_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.search_by_name.return_value = [_make_location()]

        service.search_by_name("port")
        service.search_by_name("port")

        assert repo.search_by_name.call_count == 1

    def test_search_by_name_different_queries_not_cached(self) -> None:
        service, repo = _make_service()
        repo.search_by_name.return_value = []

        service.search_by_name("port")
        service.search_by_name("lor")

        assert repo.search_by_name.call_count == 2


class TestCacheInvalidation:
    """Verify CUD operations invalidate cache."""

    def test_create_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.save.return_value = _make_location("new-1")

        service.list_all()
        service.create(_make_location(location_id=None))
        service.list_all()

        assert repo.find_all.call_count == 2

    def test_update_invalidates_cache(self) -> None:
        service, repo = _make_service()
        existing = _make_location()
        repo.find_all.return_value = [existing]
        repo.find_by_id.return_value = existing
        repo.update.return_value = existing

        service.list_all()
        service.update("loc-1", existing)
        service.list_all()

        assert repo.find_all.call_count == 2

    def test_delete_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.delete.return_value = True

        service.list_all()
        service.delete("loc-1")
        service.list_all()

        assert repo.find_all.call_count == 2

    def test_failed_delete_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.delete.return_value = False

        service.list_all()
        with pytest.raises(LocationNotFoundError):
            service.delete("missing")
        service.list_all()

        assert repo.find_all.call_count == 1

    def test_failed_update_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_all.return_value = [_make_location()]
        repo.find_by_id.return_value = None

        service.list_all()
        with pytest.raises(LocationNotFoundError):
            service.update("missing", _make_location())
        service.list_all()

        assert repo.find_all.call_count == 1
