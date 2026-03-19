"""Seed script to populate the maps-service with test locations for hauling contracts."""

import dataclasses

from src.application.ports.inbound.location_service import LocationService
from src.domain.models.location import Location

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


def seed_locations(service: LocationService) -> list[Location]:
    """Insert all seed systems and locations via *service*.

    The function is **idempotent** — it checks for existing systems
    before creating anything.  Safe to call on every app startup.

    Returns every created :class:`Location` (systems + child locations),
    or an empty list if data was already seeded.
    """
    # Idempotency guard: skip if systems already exist
    existing_systems = service.list_by_type("system")
    if existing_systems:
        return []

    created: list[Location] = []

    # 1. Create systems first so we can reference their IDs
    system_ids: dict[str, str] = {}
    for system in SYSTEMS:
        saved = service.create(dataclasses.replace(system))
        if saved.id is None:
            raise ValueError(f"LocationService.create returned a Location without an id for system '{saved.name}'")
        system_ids[saved.name] = saved.id
        created.append(saved)

    # 2. Create child locations with parent_id set
    for location in build_locations(system_ids):
        created.append(service.create(location))

    return created


if __name__ == "__main__":
    from opyoid import Injector

    from src.infrastructure.config.dependencies import AppModule
    from src.infrastructure.config.settings import Settings

    settings = Settings()
    injector = Injector([AppModule(settings)])
    location_service = injector.inject(LocationService)
    created = seed_locations(location_service)
    print(f"Seeded {len(created)} locations.")
    for loc in created:
        print(f"  [{loc.location_type}] {loc.name} (id={loc.id})")
