"""Seed script to populate the maps-service with test locations for hauling contracts."""

from src.application.ports.inbound.location_service import LocationService
from src.domain.models.location import Coordinates, Location

# ---------------------------------------------------------------------------
# Seed data – star systems
# ---------------------------------------------------------------------------

SYSTEMS: list[Location] = [
    Location(name="Stanton", location_type="system"),
    Location(name="Pyro", location_type="system"),
]

# ---------------------------------------------------------------------------
# Seed data – locations (parent_id is set at runtime after systems are created)
# Each tuple: (name, system_name, location_type, coordinates,
#               has_trade_terminal, has_landing_pad, landing_pad_size)
# ---------------------------------------------------------------------------

_LOCATION_DEFS: list[tuple[str, str, str, Coordinates, bool, bool, str | None]] = [
    ("Port Olisar", "Stanton", "orbital", Coordinates(x=0.0, y=0.0, z=0.0), True, True, "large"),
    ("Area18", "Stanton", "city", Coordinates(x=22.6, y=-127.0, z=10.3), True, True, "large"),
    ("Lorville", "Stanton", "city", Coordinates(x=-63.2, y=14.8, z=-7.5), True, True, "large"),
    ("New Babbage", "Stanton", "city", Coordinates(x=45.1, y=88.3, z=-22.0), True, True, "large"),
    ("GrimHEX", "Stanton", "station", Coordinates(x=-18.9, y=5.4, z=33.7), True, True, "medium"),
    ("CRU-L1", "Stanton", "orbital", Coordinates(x=100.0, y=50.0, z=0.0), True, True, "large"),
    ("HUR-L1", "Stanton", "orbital", Coordinates(x=-50.0, y=75.0, z=12.0), True, True, "large"),
    ("Ruin Station", "Pyro", "station", Coordinates(x=200.0, y=-10.0, z=5.0), True, True, "medium"),
    ("Pyro Gateway", "Pyro", "station", Coordinates(x=180.0, y=0.0, z=0.0), True, True, "large"),
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
            coordinates=coords,
            has_trade_terminal=trade,
            has_landing_pad=pad,
            landing_pad_size=pad_size,
        )
        for name, system_name, loc_type, coords, trade, pad, pad_size in _LOCATION_DEFS
    ]


def seed_locations(service: LocationService) -> list[Location]:
    """Insert all seed systems and locations via *service*.

    Returns every created :class:`Location` (systems + child locations).
    """
    created: list[Location] = []

    # 1. Create systems first so we can reference their IDs
    system_ids: dict[str, str] = {}
    for system in SYSTEMS:
        saved = service.create(system)
        system_ids[saved.name] = saved.id  # type: ignore[arg-type]
        created.append(saved)

    # 2. Create child locations with parent_id set
    for location in build_locations(system_ids):
        created.append(service.create(location))

    return created
