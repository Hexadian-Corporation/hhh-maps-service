"""Seed script to populate the maps-service with test locations for hauling contracts."""

import asyncio
import dataclasses
import math

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.application.ports.inbound.location_service import LocationService
from src.domain.models.location import Location
from src.domain.models.location_distance import LocationDistance

# ---------------------------------------------------------------------------
# Seed data – star systems
# ---------------------------------------------------------------------------

SYSTEMS: list[Location] = [
    Location(name="Stanton", location_type="system"),
    Location(name="Pyro", location_type="system"),
]

# ---------------------------------------------------------------------------
# Seed data – locations (parent_id is set at runtime after systems are created)
# Each tuple: (name, system_name, location_type,
#               has_trade_terminal, has_landing_pad, landing_pad_size)
# ---------------------------------------------------------------------------

_LOCATION_DEFS: list[tuple[str, str, str, bool, bool, str | None]] = [
    ("Port Olisar", "Stanton", "orbital", True, True, "large"),
    ("Area18", "Stanton", "city", True, True, "large"),
    ("Lorville", "Stanton", "city", True, True, "large"),
    ("New Babbage", "Stanton", "city", True, True, "large"),
    ("GrimHEX", "Stanton", "station", True, True, "medium"),
    ("CRU-L1", "Stanton", "orbital", True, True, "large"),
    ("HUR-L1", "Stanton", "orbital", True, True, "large"),
    ("Ruin Station", "Pyro", "station", True, True, "medium"),
    ("Pyro Gateway", "Pyro", "station", True, True, "large"),
]


def build_locations(system_ids: dict[str, str]) -> list[Location]:
    """Build Location objects with parent_id resolved from *system_ids*.

    Parameters
    ----------
    system_ids:
        Mapping of system name → id (e.g. ``{"Stanton": "abc123", ...}``).

    Returns
    -------
    list[Location]
        Location domain objects ready to be persisted.
    """
    return [
        Location(
            name=name,
            location_type=loc_type,
            parent_id=system_ids[system_name],
            has_trade_terminal=trade,
            has_landing_pad=pad,
            landing_pad_size=pad_size,
        )
        for name, system_name, loc_type, trade, pad, pad_size in _LOCATION_DEFS
    ]


async def seed_locations(service: LocationService) -> list[Location]:
    """Insert all seed systems and locations via *service*.

    The function is **idempotent** — it checks for existing systems
    before creating anything.  Safe to call on every app startup.

    Returns every created :class:`Location` (systems + child locations),
    or an empty list if data was already seeded.
    """
    # Idempotency guard: skip if systems already exist
    existing_systems = await service.list_by_type("system")
    if existing_systems:
        return []

    # 1. Create systems in parallel so we can reference their IDs
    created_systems = await asyncio.gather(*[service.create(dataclasses.replace(system)) for system in SYSTEMS])
    for saved in created_systems:
        if saved.id is None:
            raise ValueError(f"LocationService.create returned a Location without an id for system '{saved.name}'")

    system_ids: dict[str, str] = {saved.name: saved.id for saved in created_systems}

    # 2. Create child locations in parallel with parent_id set
    created_children = await asyncio.gather(*[service.create(location) for location in build_locations(system_ids)])

    return list(created_systems) + list(created_children)


# ---------------------------------------------------------------------------
# Seed data – location coordinates (km, relative to star-system centre)
# Used exclusively for distance calculations; not stored on the Location model.
# ---------------------------------------------------------------------------

_LOCATION_COORDS: dict[str, tuple[float, float, float]] = {
    # Stanton system locations
    "Port Olisar": (0.0, 0.0, 0.0),
    "Area18": (12_875.0, 0.0, 0.0),
    "Lorville": (-19_467.0, 0.0, 0.0),
    "New Babbage": (0.0, 22_462.0, 0.0),
    "GrimHEX": (0.0, -8_500.0, 3_200.0),
    "CRU-L1": (38_000.0, 0.0, 0.0),
    "HUR-L1": (-35_000.0, 0.0, 0.0),
    # Pyro system locations (offset to simulate inter-system distances)
    "Ruin Station": (150_000.0, 0.0, 0.0),
    "Pyro Gateway": (175_000.0, 25_000.0, 0.0),
}


def compute_distance(coord_a: tuple[float, float, float], coord_b: tuple[float, float, float]) -> float:
    """Euclidean distance in km between two (x, y, z) coordinate tuples."""
    return math.sqrt((coord_a[0] - coord_b[0]) ** 2 + (coord_a[1] - coord_b[1]) ** 2 + (coord_a[2] - coord_b[2]) ** 2)


async def seed_distances(
    location_service: LocationService,
    distance_service: LocationDistanceService,
) -> list[LocationDistance]:
    """Compute and seed distances between all trade terminal locations.

    The function is **idempotent** — it checks for existing distance records
    before creating anything.  Safe to call on every app startup.

    For each unique pair of trade-terminal locations two records are created:
    one for quantum travel and one for SCM travel.

    Returns every created :class:`LocationDistance`, or an empty list if
    records already exist.
    """
    if await distance_service.list_all():
        return []

    locations = await location_service.list_all()
    trade_locations = [loc for loc in locations if loc.has_trade_terminal and loc.id is not None]

    to_create: list[LocationDistance] = []
    for i, loc_a in enumerate(trade_locations):
        for loc_b in trade_locations[i + 1 :]:
            coord_a = _LOCATION_COORDS.get(loc_a.name)
            coord_b = _LOCATION_COORDS.get(loc_b.name)
            if coord_a is None or coord_b is None:
                continue

            dist_km = compute_distance(coord_a, coord_b)

            for travel_type in ("quantum", "scm"):
                to_create.append(
                    LocationDistance(
                        from_location_id=loc_a.id,
                        to_location_id=loc_b.id,
                        distance=round(dist_km * 1000, 2),  # store in metres
                        travel_type=travel_type,
                    )
                )

    created = await asyncio.gather(*[distance_service.create(ld) for ld in to_create])
    return list(created)


if __name__ == "__main__":
    from opyoid import Injector

    from src.infrastructure.config.dependencies import AppModule
    from src.infrastructure.config.settings import Settings

    async def _main() -> None:
        settings = Settings()
        module = AppModule(settings)
        injector = Injector([module])
        await module.create_indexes()
        location_service = injector.inject(LocationService)
        created = await seed_locations(location_service)
        print(f"Seeded {len(created)} locations.")
        for loc in created:
            print(f"  [{loc.location_type}] {loc.name} (id={loc.id})")

    asyncio.run(_main())
