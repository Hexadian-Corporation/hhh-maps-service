"""Unit tests for LocationDistanceServiceImpl TTL cache behavior."""

from unittest.mock import AsyncMock

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


def _make_service(repo: AsyncMock | None = None) -> tuple[LocationDistanceServiceImpl, AsyncMock]:
    repo = repo or AsyncMock()
    return LocationDistanceServiceImpl(repo), repo


class TestGetNotFound:
    @pytest.mark.anyio
    async def test_get_raises_when_not_found(self) -> None:
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(LocationDistanceNotFoundError):
            await service.get("missing")

    @pytest.mark.anyio
    async def test_get_by_pair_raises_when_not_found(self) -> None:
        service, repo = _make_service()
        repo.find_by_pair.return_value = None

        with pytest.raises(LocationDistanceNotFoundError):
            await service.get_by_pair("loc-a", "loc-b")


class TestCacheHit:
    """Verify second call within TTL returns cached result (repo not called again)."""

    @pytest.mark.anyio
    async def test_get_by_location_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]

        await service.get_by_location("loc-a")
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1

    @pytest.mark.anyio
    async def test_get_by_location_different_ids_not_cached(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = []

        await service.get_by_location("loc-a")
        await service.get_by_location("loc-b")

        assert repo.find_by_location.call_count == 2

    @pytest.mark.anyio
    async def test_get_by_pair_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_pair.return_value = _make_distance()

        await service.get_by_pair("loc-a", "loc-b")
        await service.get_by_pair("loc-a", "loc-b")

        assert repo.find_by_pair.call_count == 1

    @pytest.mark.anyio
    async def test_get_by_pair_normalized_key(self) -> None:
        """A→B and B→A should hit the same cache entry."""
        service, repo = _make_service()
        repo.find_by_pair.return_value = _make_distance()

        await service.get_by_pair("loc-a", "loc-b")
        await service.get_by_pair("loc-b", "loc-a")

        assert repo.find_by_pair.call_count == 1


class TestCacheInvalidation:
    """Verify CUD operations invalidate cache."""

    @pytest.mark.anyio
    async def test_create_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.save.return_value = _make_distance("dist-2")

        await service.get_by_location("loc-a")
        await service.create(_make_distance(distance_id=None))
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    @pytest.mark.anyio
    async def test_update_invalidates_cache(self) -> None:
        service, repo = _make_service()
        existing = _make_distance()
        repo.find_by_location.return_value = [existing]
        repo.find_by_id.return_value = existing
        repo.update.return_value = existing

        await service.get_by_location("loc-a")
        await service.update("dist-1", existing)
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    @pytest.mark.anyio
    async def test_delete_invalidates_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.delete.return_value = True

        await service.get_by_location("loc-a")
        await service.delete("dist-1")
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 2

    @pytest.mark.anyio
    async def test_failed_delete_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.delete.return_value = False

        await service.get_by_location("loc-a")
        with pytest.raises(LocationDistanceNotFoundError):
            await service.delete("missing")
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1

    @pytest.mark.anyio
    async def test_failed_update_does_not_invalidate_cache(self) -> None:
        service, repo = _make_service()
        repo.find_by_location.return_value = [_make_distance()]
        repo.find_by_id.return_value = None

        await service.get_by_location("loc-a")
        with pytest.raises(LocationDistanceNotFoundError):
            await service.update("missing", _make_distance())
        await service.get_by_location("loc-a")

        assert repo.find_by_location.call_count == 1


class TestListByTravelType:
    """Verify list_by_travel_type caches results per travel_type."""

    @pytest.mark.anyio
    async def test_list_by_travel_type_returns_matching_distances(self) -> None:
        service, repo = _make_service()
        repo.find_by_travel_type.return_value = [_make_distance()]

        result = await service.list_by_travel_type("wormhole")

        assert len(result) == 1
        repo.find_by_travel_type.assert_called_once_with("wormhole")

    @pytest.mark.anyio
    async def test_list_by_travel_type_cached_on_second_call(self) -> None:
        service, repo = _make_service()
        repo.find_by_travel_type.return_value = [_make_distance()]

        await service.list_by_travel_type("wormhole")
        await service.list_by_travel_type("wormhole")

        assert repo.find_by_travel_type.call_count == 1

    @pytest.mark.anyio
    async def test_list_by_travel_type_different_keys_not_shared(self) -> None:
        service, repo = _make_service()
        repo.find_by_travel_type.return_value = []

        await service.list_by_travel_type("wormhole")
        await service.list_by_travel_type("quantum")

        assert repo.find_by_travel_type.call_count == 2

    @pytest.mark.anyio
    async def test_list_by_travel_type_cache_invalidated_on_create(self) -> None:
        service, repo = _make_service()
        repo.find_by_travel_type.return_value = [_make_distance()]
        repo.save.return_value = _make_distance("dist-new")

        await service.list_by_travel_type("wormhole")
        await service.create(_make_distance(distance_id=None))
        await service.list_by_travel_type("wormhole")

        assert repo.find_by_travel_type.call_count == 2
