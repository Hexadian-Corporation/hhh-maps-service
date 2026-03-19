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
def create_distance(dto: LocationDistanceCreateDTO) -> LocationDistanceDTO:
    distance = LocationDistanceApiMapper.create_to_domain(dto)
    created = _distance_service.create(distance)
    return LocationDistanceApiMapper.to_dto(created)


@distance_router.get("/distances/", response_model=LocationDistanceDTO | None, dependencies=_read)
def get_distance_by_pair(from_location_id: str, to_location_id: str, response: Response) -> LocationDistanceDTO:
    try:
        distance = _distance_service.get_by_pair(from_location_id, to_location_id)
    except LocationDistanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    return LocationDistanceApiMapper.to_dto(distance)


@distance_router.put("/distances/{distance_id}", response_model=LocationDistanceDTO, dependencies=_write)
def update_distance(distance_id: str, dto: LocationDistanceUpdateDTO) -> LocationDistanceDTO:
    try:
        existing = _distance_service.get(distance_id)
    except LocationDistanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    merged = LocationDistanceApiMapper.update_to_domain(dto, existing)
    updated = _distance_service.update(distance_id, merged)
    return LocationDistanceApiMapper.to_dto(updated)


@distance_router.delete("/distances/{distance_id}", status_code=204, dependencies=_delete)
def delete_distance(distance_id: str) -> None:
    try:
        _distance_service.delete(distance_id)
    except LocationDistanceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- /locations/{id}/distances endpoint ---


@distance_router.get(
    "/locations/{location_id}/distances",
    response_model=list[LocationDistanceDTO],
    dependencies=_read,
)
def get_distances_from_location(location_id: str, response: Response) -> list[LocationDistanceDTO]:
    distances = _distance_service.get_by_location(location_id)
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    return [LocationDistanceApiMapper.to_dto(d) for d in distances]
