"""Integration tests for Location search and filter endpoints."""

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
    }
    response = await client.post("/locations/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# TestLocationSearch
# ---------------------------------------------------------------------------


class TestLocationSearch:
    """Integration tests for GET /locations/search?q=."""

    @pytest.mark.anyio
    async def test_search_exact_name_finds_location(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=Lorville")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Lorville"

    @pytest.mark.anyio
    async def test_search_partial_name_finds_matching_locations(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Port Olisar", location_type="station")
        await _create(api_client, name="Port Tressler", location_type="station")
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=Port")

        assert response.status_code == 200
        data = response.json()
        names = {loc["name"] for loc in data}
        assert "Port Olisar" in names
        assert "Port Tressler" in names
        assert "Lorville" not in names

    @pytest.mark.anyio
    async def test_search_case_insensitive(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=lorville")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Lorville"

    @pytest.mark.anyio
    async def test_search_no_results_returns_empty_list(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=NonExistentXyz")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_search_special_characters_no_error(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/locations/search?q=.*+?[](){}\\^$|")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.anyio
    async def test_search_empty_string_returns_empty_list(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_search_no_query_param_returns_empty_list(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_search_multiple_matching_locations(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Area18", location_type="city")
        await _create(api_client, name="Area19", location_type="city")
        await _create(api_client, name="Area20", location_type="city")
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/search?q=Area")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        names = {loc["name"] for loc in data}
        assert names == {"Area18", "Area19", "Area20"}


# ---------------------------------------------------------------------------
# TestLocationFilterByType
# ---------------------------------------------------------------------------


class TestLocationFilterByType:
    """Integration tests for GET /locations/?location_type=."""

    @pytest.mark.anyio
    async def test_filter_by_planet_returns_only_planets(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="ArcCorp", location_type="planet")
        await _create(api_client, name="Crusader", location_type="planet")
        await _create(api_client, name="Cellin", location_type="moon")

        response = await api_client.get("/locations/?location_type=planet")

        assert response.status_code == 200
        data = response.json()
        assert all(loc["location_type"] == "planet" for loc in data)
        names = {loc["name"] for loc in data}
        assert "ArcCorp" in names
        assert "Crusader" in names
        assert "Cellin" not in names

    @pytest.mark.anyio
    async def test_filter_by_moon_returns_only_moons(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Crusader", location_type="planet")
        await _create(api_client, name="Cellin", location_type="moon")
        await _create(api_client, name="Daymar", location_type="moon")

        response = await api_client.get("/locations/?location_type=moon")

        assert response.status_code == 200
        data = response.json()
        assert all(loc["location_type"] == "moon" for loc in data)
        names = {loc["name"] for loc in data}
        assert "Cellin" in names
        assert "Daymar" in names
        assert "Crusader" not in names

    @pytest.mark.anyio
    async def test_filter_by_nonexistent_type_returns_empty(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Lorville", location_type="city")

        response = await api_client.get("/locations/?location_type=nonexistent_type")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_filter_returns_all_locations_of_requested_type(self, api_client: AsyncClient) -> None:
        planet_names = ["ArcCorp", "Crusader", "MicroTech", "Hurston"]
        for name in planet_names:
            await _create(api_client, name=name, location_type="planet")
        await _create(api_client, name="Cellin", location_type="moon")

        response = await api_client.get("/locations/?location_type=planet")

        assert response.status_code == 200
        data = response.json()
        returned_names = {loc["name"] for loc in data}
        assert set(planet_names) == returned_names


# ---------------------------------------------------------------------------
# TestLocationFilterByParent
# ---------------------------------------------------------------------------


class TestLocationFilterByParent:
    """Integration tests for GET /locations/?parent_id={id}."""

    @pytest.mark.anyio
    async def test_filter_by_parent_id_returns_only_children(self, api_client: AsyncClient) -> None:
        parent = await _create(api_client, name="Crusader", location_type="planet")
        parent_id = parent["_id"]
        await _create(api_client, name="Cellin", location_type="moon", parent_id=parent_id)
        await _create(api_client, name="Daymar", location_type="moon", parent_id=parent_id)

        other_parent = await _create(api_client, name="ArcCorp", location_type="planet")
        await _create(api_client, name="Lyria", location_type="moon", parent_id=other_parent["_id"])

        response = await api_client.get(f"/locations/?parent_id={parent_id}")

        assert response.status_code == 200
        data = response.json()
        assert all(loc["parent_id"] == parent_id for loc in data)
        names = {loc["name"] for loc in data}
        assert "Cellin" in names
        assert "Daymar" in names
        assert "Lyria" not in names

    @pytest.mark.anyio
    async def test_filter_by_nonexistent_parent_returns_empty(self, api_client: AsyncClient) -> None:
        await _create(api_client, name="Cellin", location_type="moon")

        response = await api_client.get("/locations/?parent_id=000000000000000000000000")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.anyio
    async def test_parent_with_multiple_children_returns_all(self, api_client: AsyncClient) -> None:
        parent = await _create(api_client, name="Crusader", location_type="planet")
        parent_id = parent["_id"]
        child_names = ["Cellin", "Daymar", "Yela"]
        for name in child_names:
            await _create(api_client, name=name, location_type="moon", parent_id=parent_id)

        response = await api_client.get(f"/locations/?parent_id={parent_id}")

        assert response.status_code == 200
        data = response.json()
        returned_names = {loc["name"] for loc in data}
        assert set(child_names) == returned_names


# ---------------------------------------------------------------------------
# TestLocationFilterCombinations
# ---------------------------------------------------------------------------


class TestLocationFilterCombinations:
    """Integration tests for combined location_type + parent_id filters."""

    @pytest.mark.anyio
    async def test_combined_filters_return_correct_intersection(self, api_client: AsyncClient) -> None:
        crusader = await _create(api_client, name="Crusader", location_type="planet")
        crusader_id = crusader["_id"]

        arccorp = await _create(api_client, name="ArcCorp", location_type="planet")
        arccorp_id = arccorp["_id"]

        # Moons of Crusader
        await _create(api_client, name="Cellin", location_type="moon", parent_id=crusader_id)
        await _create(api_client, name="Daymar", location_type="moon", parent_id=crusader_id)

        # Moon of ArcCorp
        await _create(api_client, name="Lyria", location_type="moon", parent_id=arccorp_id)

        # Station orbiting Crusader (same parent, different type)
        await _create(api_client, name="Orison", location_type="city", parent_id=crusader_id)

        response = await api_client.get(f"/locations/?location_type=moon&parent_id={crusader_id}")

        assert response.status_code == 200
        data = response.json()
        names = {loc["name"] for loc in data}
        assert names == {"Cellin", "Daymar"}
        assert "Lyria" not in names
        assert "Orison" not in names

    @pytest.mark.anyio
    async def test_combined_filters_no_match_returns_empty(self, api_client: AsyncClient) -> None:
        parent = await _create(api_client, name="Crusader", location_type="planet")
        parent_id = parent["_id"]
        await _create(api_client, name="Cellin", location_type="moon", parent_id=parent_id)

        # Ask for 'system' type under that parent — no match
        response = await api_client.get(f"/locations/?location_type=system&parent_id={parent_id}")

        assert response.status_code == 200
        assert response.json() == []
