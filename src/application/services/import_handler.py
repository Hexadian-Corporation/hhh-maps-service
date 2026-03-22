"""Processes incoming bulk import events for locations and distances."""

import logging
import re

from hhh_events import EventDocument, EventMode, EventPublisher

from src.application.ports.outbound.location_distance_repository import LocationDistanceRepository
from src.application.ports.outbound.location_repository import LocationRepository
from src.domain.models.location import Location
from src.domain.models.location_distance import LocationDistance

logger = logging.getLogger(__name__)

_UEX_PREFIX = re.compile(r"^uex:location:")


class LocationImportHandler:
    """Upserts locations received via dataminer events."""

    def __init__(self, repository: LocationRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    async def handle(self, event: EventDocument) -> int:
        items = event.metadata.get("items", [])
        changed_ids: list[str] = []
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            location = Location(
                name=name,
                location_type=item.get("type", ""),
                in_game=True,
            )
            entity, changed = await self._repository.upsert_by_name(location)
            if changed:
                changed_ids.append(entity.id)
        if changed_ids:
            await self._publisher.publish(
                EventDocument(
                    type="locations.imported",
                    source_service="maps-service",
                    modified_ids=changed_ids,
                    mode=EventMode.INCREMENTAL,
                ),
            )
        logger.info("Imported %d locations with key changes from event", len(changed_ids))
        return len(changed_ids)


class DistanceImportHandler:
    """Upserts distances received via dataminer events."""

    def __init__(
        self,
        distance_repository: LocationDistanceRepository,
        location_repository: LocationRepository,
        publisher: EventPublisher,
    ) -> None:
        self._distance_repository = distance_repository
        self._location_repository = location_repository
        self._publisher = publisher

    async def handle(self, event: EventDocument) -> int:
        items = event.metadata.get("items", [])
        changed_ids: list[str] = []
        for item in items:
            from_name = _UEX_PREFIX.sub("", item.get("from_id", ""))
            to_name = _UEX_PREFIX.sub("", item.get("to_id", ""))
            if not from_name or not to_name:
                continue

            from_loc = await self._resolve_location(from_name)
            to_loc = await self._resolve_location(to_name)
            if not from_loc or not to_loc:
                continue

            distance = LocationDistance(
                from_location_id=from_loc,
                to_location_id=to_loc,
                distance=float(item.get("distance", 0)),
                travel_type=item.get("travel_type", "quantum"),
                in_game=True,
            )
            entity, changed = await self._distance_repository.upsert_by_pair(distance)
            if changed:
                changed_ids.append(entity.id)
        if changed_ids:
            await self._publisher.publish(
                EventDocument(
                    type="distances.imported",
                    source_service="maps-service",
                    modified_ids=changed_ids,
                    mode=EventMode.INCREMENTAL,
                ),
            )
        logger.info("Imported %d distances with key changes from event", len(changed_ids))
        return len(changed_ids)

    async def _resolve_location(self, name: str) -> str | None:
        results = await self._location_repository.search_by_name(name)
        for loc in results:
            if loc.name.lower() == name.lower():
                return loc.id
        return None
