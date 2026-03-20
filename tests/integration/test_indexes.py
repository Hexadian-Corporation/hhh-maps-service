"""Integration tests for MongoDB indexes on locations and location_distances collections."""

import pytest
from pymongo import MongoClient
from pymongo.collection import Collection

from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings

_LOCATIONS_COL = "locations"
_DISTANCES_COL = "location_distances"


# ─── Shared fixture ────────────────────────────────────────────────────────────


@pytest.fixture()
def configured_collections(mongo_container) -> tuple[Collection, Collection]:
    """Run AppModule.configure() on a fresh DB and return (locations, distances)."""
    db_name = "hhh_maps_indexes_test"
    mongo_uri = mongo_container.get_connection_url()

    # Start with clean collections
    client = MongoClient(mongo_uri)
    client[db_name][_LOCATIONS_COL].drop()
    client[db_name][_DISTANCES_COL].drop()
    client.close()

    AppModule(Settings(mongo_uri=mongo_uri, mongo_db=db_name)).configure()

    client = MongoClient(mongo_uri)
    db = client[db_name]
    yield db[_LOCATIONS_COL], db[_DISTANCES_COL]
    db[_LOCATIONS_COL].drop()
    db[_DISTANCES_COL].drop()
    client.close()


# ─── TestLocationIndexes ───────────────────────────────────────────────────────


class TestLocationIndexes:
    """Verify all indexes on the 'locations' collection."""

    def test_all_expected_index_names_exist(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        index_names = set(location_col.index_information().keys())
        assert "location_type_1" in index_names
        assert "parent_id_1" in index_names
        assert "name_1" in index_names

    def test_location_type_index_key(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert info["location_type_1"]["key"] == [("location_type", 1)]

    def test_parent_id_index_key(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert info["parent_id_1"]["key"] == [("parent_id", 1)]

    def test_name_index_key(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert info["name_1"]["key"] == [("name", 1)]

    def test_name_index_has_collation(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert "collation" in info["name_1"]
        collation = info["name_1"]["collation"]
        assert collation["locale"] == "en"
        assert collation["strength"] == 2

    def test_location_type_index_is_not_unique(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert not info["location_type_1"].get("unique", False)

    def test_parent_id_index_is_not_unique(self, configured_collections: tuple) -> None:
        location_col, _ = configured_collections
        info = location_col.index_information()
        assert not info["parent_id_1"].get("unique", False)

    def test_idempotency(self, mongo_container) -> None:
        """Calling AppModule.configure() twice on the same collection must not raise."""
        db_name = "hhh_maps_idempotency_locations_test"
        mongo_uri = mongo_container.get_connection_url()

        client = MongoClient(mongo_uri)
        client[db_name][_LOCATIONS_COL].drop()
        client.close()

        settings = Settings(mongo_uri=mongo_uri, mongo_db=db_name)
        AppModule(settings).configure()
        AppModule(settings).configure()  # second call — must not raise


# ─── TestDistanceIndexes ───────────────────────────────────────────────────────


class TestDistanceIndexes:
    """Verify all indexes on the 'location_distances' collection."""

    def test_all_expected_index_names_exist(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        index_names = set(distance_col.index_information().keys())
        assert "from_location_id_1_to_location_id_1_travel_type_1" in index_names
        assert "from_location_id_1" in index_names
        assert "to_location_id_1" in index_names

    def test_compound_index_key(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        compound = info["from_location_id_1_to_location_id_1_travel_type_1"]
        assert compound["key"] == [("from_location_id", 1), ("to_location_id", 1), ("travel_type", 1)]

    def test_compound_index_is_unique(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        assert info["from_location_id_1_to_location_id_1_travel_type_1"].get("unique") is True

    def test_from_location_id_index_key(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        assert info["from_location_id_1"]["key"] == [("from_location_id", 1)]

    def test_from_location_id_index_is_not_unique(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        assert not info["from_location_id_1"].get("unique", False)

    def test_to_location_id_index_key(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        assert info["to_location_id_1"]["key"] == [("to_location_id", 1)]

    def test_to_location_id_index_is_not_unique(self, configured_collections: tuple) -> None:
        _, distance_col = configured_collections
        info = distance_col.index_information()
        assert not info["to_location_id_1"].get("unique", False)

    def test_idempotency(self, mongo_container) -> None:
        """Calling AppModule.configure() twice on the same collection must not raise."""
        db_name = "hhh_maps_idempotency_distances_test"
        mongo_uri = mongo_container.get_connection_url()

        client = MongoClient(mongo_uri)
        client[db_name][_DISTANCES_COL].drop()
        client.close()

        settings = Settings(mongo_uri=mongo_uri, mongo_db=db_name)
        AppModule(settings).configure()
        AppModule(settings).configure()  # second call — must not raise


# ─── TestIndexCreation ────────────────────────────────────────────────────────


class TestIndexCreation:
    """Verify indexes are automatically created when the application is configured."""

    def test_appmodule_creates_location_indexes_on_clean_collection(self, mongo_container) -> None:
        """AppModule.configure() on a fresh collection creates all location indexes."""
        db_name = "hhh_maps_creation_locations_test"
        mongo_uri = mongo_container.get_connection_url()

        client = MongoClient(mongo_uri)
        client[db_name][_LOCATIONS_COL].drop()
        client.close()

        AppModule(Settings(mongo_uri=mongo_uri, mongo_db=db_name)).configure()

        client = MongoClient(mongo_uri)
        index_names = set(client[db_name][_LOCATIONS_COL].index_information().keys())
        client.close()

        assert "location_type_1" in index_names
        assert "parent_id_1" in index_names
        assert "name_1" in index_names

    def test_appmodule_creates_distance_indexes_on_clean_collection(self, mongo_container) -> None:
        """AppModule.configure() on a fresh collection creates all distance indexes."""
        db_name = "hhh_maps_creation_distances_test"
        mongo_uri = mongo_container.get_connection_url()

        client = MongoClient(mongo_uri)
        client[db_name][_DISTANCES_COL].drop()
        client.close()

        AppModule(Settings(mongo_uri=mongo_uri, mongo_db=db_name)).configure()

        client = MongoClient(mongo_uri)
        index_names = set(client[db_name][_DISTANCES_COL].index_information().keys())
        client.close()

        assert "from_location_id_1_to_location_id_1_travel_type_1" in index_names
        assert "from_location_id_1" in index_names
        assert "to_location_id_1" in index_names

    def test_full_app_creates_indexes_on_both_collections(self, mongo_container, monkeypatch) -> None:
        """create_app() configures both collections with their respective indexes."""
        db_name = "hhh_maps_full_app_indexes_test"
        mongo_uri = mongo_container.get_connection_url()

        monkeypatch.setenv("HHH_MAPS_MONGO_URI", mongo_uri)
        monkeypatch.setenv("HHH_MAPS_MONGO_DB", db_name)

        client = MongoClient(mongo_uri)
        client[db_name][_LOCATIONS_COL].drop()
        client[db_name][_DISTANCES_COL].drop()
        client.close()

        from src.main import create_app

        create_app()

        client = MongoClient(mongo_uri)
        db = client[db_name]
        location_index_names = set(db[_LOCATIONS_COL].index_information().keys())
        distance_index_names = set(db[_DISTANCES_COL].index_information().keys())
        client.close()

        assert "location_type_1" in location_index_names
        assert "parent_id_1" in location_index_names
        assert "name_1" in location_index_names

        assert "from_location_id_1_to_location_id_1_travel_type_1" in distance_index_names
        assert "from_location_id_1" in distance_index_names
        assert "to_location_id_1" in distance_index_names
