"""Integration tests for Location CRUD API endpoints."""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create(client: AsyncClient, **kwargs) -> dict:
    """POST /locations/ and return the created location JSON."""
    payload = {
        "name": kwargs.get("name", "Test Location"),
        "location_type": kwargs.get("location_type", "planet"),
        "parent_id": kwargs.get("parent_id"),
        "has_trade_terminal": kwargs.get("has_trade_terminal", False),
        "has_landing_pad": kwargs.get("has_landing_pad", False),
        "landing_pad_size": kwargs.get("landing_pad_size"),
        "in_game": kwargs.get("in_game", True),
    }
    response = await client.post("/locations/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# TestPostLocation
# ---------------------------------------------------------------------------


class TestPostLocation:
    """Tests for POST /locations/."""

    @pytest.mark.anyio
    async def test_create_location_with_all_fields(self, api_client: AsyncClient) -> None:
        payload = {
            "name": "Lorville",
            "location_type": "city",
            "parent_id": "507f1f77bcf86cd799439011",
            "has_trade_terminal": True,
            "has_landing_pad": True,
            "landing_pad_size": "large",
            "in_game": True,
        }
        response = await api_client.post("/locations/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Lorville"
        assert data["location_type"] == "city"
        assert data["parent_id"] == "507f1f77bcf86cd799439011"
        assert data["has_trade_terminal"] is True
        assert data["has_landing_pad"] is True
        assert data["landing_pad_size"] == "large"
        assert data["in_game"] is True

    @pytest.mark.anyio
    async def test_create_location_with_minimal_fields(self, api_client: AsyncClient) -> None:
        payload = {"name": "Stanton", "location_type": "system"}
        response = await api_client.post("/locations/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Stanton"
        assert data["location_type"] == "system"
        assert data["parent_id"] is None
        assert data["has_trade_terminal"] is False
        assert data["has_landing_pad"] is False
        assert data["landing_pad_size"] is None
        assert data["in_game"] is True

    @pytest.mark.anyio
    async def test_create_multiple_locations(self, api_client: AsyncClient) -> None:
        names = ["Stanton", "Pyro", "Nyx"]
        for name in names:
            resp = await api_client.post("/locations/", json={"name": name, "location_type": "system"})
            assert resp.status_code == 201

        response = await api_client.get("/locations/")
        assert len(response.json()) == 3

    @pytest.mark.anyio
    async def test_create_location_generates_id(self, api_client: AsyncClient) -> None:
        data = await _create(api_client, name="Crusader", location_type="planet")

        assert data["_id"] is not None
        assert isinstance(data["_id"], str)
        assert len(data["_id"]) > 0

    @pytest.mark.anyio
    async def test_create_generates_unique_ids(self, api_client: AsyncClient) -> None:
        loc1 = await _create(api_client, name="ArcCorp", location_type="planet")
        loc2 = await _create(api_client, name="Hurston", location_type="planet")

        assert loc1["_id"] != loc2["_id"]

    @pytest.mark.anyio
    async def test_create_returns_201_status_code(self, api_client: AsyncClient) -> None:
        response = await api_client.post("/locations/", json={"name": "Test", "location_type": "planet"})

        assert response.status_code == 201


# ---------------------------------------------------------------------------
# TestGetLocations
# ---------------------------------------------------------------------------


class TestGetLocations:
    """Tests for GET /locations/ (list all)."""

    @pytest.mark.anyio
    async def test_get_empty_list(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_get_list_with_multiple_locations(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Stanton", location_type="system")
        await _create(api_client, name="Crusader", location_type="planet")
        await _create(api_client, name="Cellin", location_type="moon")

        response = await api_client.get("/locations/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        names = {loc["name"] for loc in data}
        assert names == {"Stanton", "Crusader", "Cellin"}

    @pytest.mark.anyio
    async def test_each_location_has_all_expected_fields(self, api_client: AsyncClient) -> None:
        await _create(
            api_client,
            name="Lorville",
            location_type="city",
            has_trade_terminal=True,
            has_landing_pad=True,
            landing_pad_size="large",
        )

        response = await api_client.get("/locations/")
        data = response.json()
        assert len(data) == 1

        loc = data[0]
        expected_fields = {
            "_id",
            "name",
            "location_type",
            "parent_id",
            "has_trade_terminal",
            "has_landing_pad",
            "landing_pad_size",
            "in_game",
        }
        assert expected_fields.issubset(set(loc.keys()))


# ---------------------------------------------------------------------------
# TestGetLocationById
# ---------------------------------------------------------------------------


class TestGetLocationById:
    """Tests for GET /locations/{location_id}."""

    @pytest.mark.anyio
    async def test_get_existing_location(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Hurston", location_type="planet", has_trade_terminal=True)
        location_id = created["_id"]

        response = await api_client.get(f"/locations/{location_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == location_id
        assert data["name"] == "Hurston"
        assert data["location_type"] == "planet"
        assert data["has_trade_terminal"] is True

    @pytest.mark.anyio
    async def test_get_nonexistent_location_returns_404(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/000000000000000000000000")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_with_malformed_id_returns_error(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/not-a-valid-object-id")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# TestPutLocation
# ---------------------------------------------------------------------------


class TestPutLocation:
    """Tests for PUT /locations/{location_id}."""

    @pytest.mark.anyio
    async def test_update_all_fields(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Lorville", location_type="city")
        location_id = created["_id"]

        update_payload = {
            "name": "New Lorville",
            "location_type": "station",
            "parent_id": "507f1f77bcf86cd799439011",
            "has_trade_terminal": True,
            "has_landing_pad": True,
            "landing_pad_size": "extra_large",
            "in_game": False,
        }
        response = await api_client.put(f"/locations/{location_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Lorville"
        assert data["location_type"] == "station"
        assert data["parent_id"] == "507f1f77bcf86cd799439011"
        assert data["has_trade_terminal"] is True
        assert data["has_landing_pad"] is True
        assert data["landing_pad_size"] == "extra_large"
        assert data["in_game"] is False

    @pytest.mark.anyio
    async def test_update_partial_only_name(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Lorville", location_type="city", has_trade_terminal=True)
        location_id = created["_id"]

        response = await api_client.put(f"/locations/{location_id}", json={"name": "New Lorville"})

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Lorville"
        assert data["location_type"] == "city"
        assert data["has_trade_terminal"] is True

    @pytest.mark.anyio
    async def test_update_partial_only_in_game(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Lorville", location_type="city")
        location_id = created["_id"]

        response = await api_client.put(f"/locations/{location_id}", json={"in_game": False})

        assert response.status_code == 200
        data = response.json()
        assert data["in_game"] is False
        assert data["name"] == "Lorville"

    @pytest.mark.anyio
    async def test_update_nonexistent_location_returns_404(self, api_client: AsyncClient) -> None:
        response = await api_client.put(
            "/locations/000000000000000000000000",
            json={"name": "Ghost"},
        )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_update_preserves_id(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Lorville", location_type="city")
        location_id = created["_id"]

        response = await api_client.put(f"/locations/{location_id}", json={"name": "Updated"})

        assert response.status_code == 200
        assert response.json()["_id"] == location_id

    @pytest.mark.anyio
    async def test_update_is_persisted(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Lorville", location_type="city")
        location_id = created["_id"]

        await api_client.put(f"/locations/{location_id}", json={"name": "Updated Lorville"})

        get_resp = await api_client.get(f"/locations/{location_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Updated Lorville"


# ---------------------------------------------------------------------------
# TestDeleteLocation
# ---------------------------------------------------------------------------


class TestDeleteLocation:
    """Tests for DELETE /locations/{location_id}."""

    @pytest.mark.anyio
    async def test_delete_existing_location(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Temporary", location_type="outpost")
        location_id = created["_id"]

        response = await api_client.delete(f"/locations/{location_id}")

        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_delete_nonexistent_location_returns_404(self, api_client: AsyncClient) -> None:
        response = await api_client.delete("/locations/000000000000000000000000")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_after_delete_returns_404(self, api_client: AsyncClient) -> None:
        created = await _create(api_client, name="Ephemeral", location_type="station")
        location_id = created["_id"]

        delete_resp = await api_client.delete(f"/locations/{location_id}")
        assert delete_resp.status_code == 204

        get_resp = await api_client.get(f"/locations/{location_id}")
        assert get_resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_with_malformed_id_returns_404(self, api_client: AsyncClient) -> None:
        response = await api_client.delete("/locations/not-a-valid-object-id")

        assert response.status_code == 404

        keep = await _create(api_client, name="Keeper", location_type="planet")
        remove = await _create(api_client, name="Removable", location_type="moon")

        await api_client.delete(f"/locations/{remove['_id']}")

        get_resp = await api_client.get(f"/locations/{keep['_id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Keeper"


# ---------------------------------------------------------------------------
# TestCacheControlHeaders
# ---------------------------------------------------------------------------


class TestCacheControlHeaders:
    """Verify Cache-Control headers on GET list and search responses."""

    @pytest.mark.anyio
    async def test_list_locations_has_cache_control(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/")

        assert response.status_code == 200
        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == "max-age=300"

    @pytest.mark.anyio
    async def test_search_locations_has_cache_control(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/search?q=test")

        assert response.status_code == 200
        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == "max-age=300"
