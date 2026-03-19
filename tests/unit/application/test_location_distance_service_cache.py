"""Unit tests for LocationDistanceServiceImpl TTL cache behavior."""

from unittest.mock import MagicMock

import pytest

from src.application.services.location_distance_service_impl import LocationDistanceServiceImpl
from src.domain.exceptions.location_distance_exceptions import LocationDistanceNotFoundError
from src.domain.models.location_distance import LocationDistance


def _make_distance(
    distance_id: str = "dist-1",
    from_id: str = "loc-a",
    to_id: str = "loc-b",
) -> LocationDistance:
    return LocationDistance(
        id=distance_id,
        from_location_id=from_id,
        to_location_id=to_id,
        distance=1000.0,
        travel_type="quantum",
    )


def _make_service(repo: MagicMock | None = None) -> tuple[LocationDistanceServiceImpl, MagicMock]:
    repo = repo or MagicMock()
    return LocationDistanceServiceImpl(repo), repo


class TestCacheHit:
    """Verify second call within TTL returns cached result (repo not called again)."""

    def test_get_by_location_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]

        service.get_by_location("loc-a")
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1

    def test_get_by_location_different_ids_not_cached(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = []

        service.get_by_location("loc-a")
        service.get_by_location("loc-b")

        assert repo.find_by_location.call_count == 2

    def test_get_by_pair_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_pair.return_value = _make_distance()

        service.get_by_pair("loc-a", "loc-b")
        service.get_by_pair("loc-a", "loc-b")

        assert repo.find_by_pair.call_count == 1

    def test_get_by_pair_normalized_key(self) -> None:
        """A→B and B→A should hit the same cache entry."""
        service, repo = _make_service()
        repo.find_by_pair.return_value = _make_distance()

        service.get_by_pair("loc-a", "loc-b")
        service.get_by_pair("loc-b", "loc-a")

        assert repo.find_by_pair.call_count == 1


class TestCacheInvalidation:
    """Verify CUD operations invalidate cache."""

    def test_create_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.save.return_value = _make_distance("dist-2")

        service.get_by_location("loc-a")
        service.create(_make_distance(distance_id=None))
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    def test_update_invalidates_cache(self) -> None:
        service, repo = _make_service()
        existing = _make_distance()
        repo.find_by_location.return_value = [existing]
        repo.find_by_id.return_value = existing
        repo.update.return_value = existing

        service.get_by_location("loc-a")
        service.update("dist-1", existing)
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    def test_delete_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.delete.return_value = True

        service.get_by_location("loc-a")
        service.delete("dist-1")
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    def test_failed_delete_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.delete.return_value = False

        service.get_by_location("loc-a")
        with pytest.raises(LocationDistanceNotFoundError):
            service.delete("missing")
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1

    def test_failed_update_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.find_by_id.return_value = None

        service.get_by_location("loc-a")
        with pytest.raises(LocationDistanceNotFoundError):
            service.update("missing", _make_distance())
        service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1
