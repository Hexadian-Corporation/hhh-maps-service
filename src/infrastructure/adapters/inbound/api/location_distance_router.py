from fastapi import APIRouter, Depends, HTTPException, Response
from hexadian_auth_common.fastapi import require_permission

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.domain.exceptions.location_distance_exceptions import LocationDistanceNotFoundError
from src.infrastructure.adapters.inbound.api.location_distance_api_mapper import LocationDistanceApiMapper
from src.infrastructure.adapters.inbound.api.location_distance_dto import (
    LocationDistanceCreateDTO,
    LocationDistanceDTO,
    LocationDistanceUpdateDTO,
)

distance_router = APIRouter(tags=["distances"])

_CACHE_CONTROL_MAX_AGE = "max-age=300"

_distance_service: LocationDistanceService | None = None

_read = [Depends(require_permission("hhh:locations:read"))]
_write = [Depends(require_permission("hhh:locations:write"))]
_delete = [Depends(require_permission("hhh:locations:delete"))]


def init_distance_router(service: LocationDistanceService) -> None:
    global _distance_service
    _distance_service = service


# --- /distances/ endpoints ---


@distance_router.post("/distances/", response_model=LocationDistanceDTO, status_code=201, dependencies=_write)
async def create_distance(dto: LocationDistanceCreateDTO) -> LocationDistanceDTO:
    distance = LocationDistanceApiMapper.create_to_domain(dto)
    created = await _distance_service.create(distance)
    return LocationDistanceApiMapper.to_dto(created)


@distance_router.get("/distances/", response_model=list[LocationDistanceDTO], dependencies=_read)
async def list_distances(
    from_location_id: str | None = None,
    to_location_id: str | None = None,
    travel_type: str | None = None,
    response: Response = None,
) -> list[LocationDistanceDTO]:
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    if from_location_id and to_location_id:
        try:
            distance = await _distance_service.get_by_pair(from_location_id, to_location_id)
            return [LocationDistanceApiMapper.to_dto(distance)]
        except LocationDistanceNotFoundError:
            return []
    distances = (
        await _distance_service.list_by_travel_type(travel_type) if travel_type else await _distance_service.list_all()
    )
    return [LocationDistanceApiMapper.to_dto(d) for d in distances]


@distance_router.put("/distances/{distance_id}", response_model=LocationDistanceDTO, dependencies=_write)
async def update_distance(distance_id: str, dto: LocationDistanceUpdateDTO) -> LocationDistanceDTO:
    try:
        existing = await _distance_service.get(distance_id)
    except LocationDistanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    merged = LocationDistanceApiMapper.update_to_domain(dto, existing)
    updated = await _distance_service.update(distance_id, merged)
    return LocationDistanceApiMapper.to_dto(updated)


@distance_router.delete("/distances/{distance_id}", status_code=204, dependencies=_delete)
async def delete_distance(distance_id: str) -> None:
    try:
        await _distance_service.delete(distance_id)
    except LocationDistanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- /locations/{id}/distances endpoint ---


@distance_router.get(
    "/locations/{location_id}/distances",
    response_model=list[LocationDistanceDTO],
    dependencies=_read,
)
async def get_distances_from_location(location_id: str, response: Response) -> list[LocationDistanceDTO]:
    distances = await _distance_service.get_by_location(location_id)
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    return [LocationDistanceApiMapper.to_dto(d) for d in distances]
