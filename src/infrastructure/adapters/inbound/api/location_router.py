from fastapi import APIRouter, Depends, HTTPException, Response
from hexadian_auth_common.fastapi import require_permission

from src.application.ports.inbound.location_service import LocationService
from src.domain.exceptions.location_exceptions import LocationNotFoundError
from src.infrastructure.adapters.inbound.api.location_api_mapper import LocationApiMapper
from src.infrastructure.adapters.inbound.api.location_dto import LocationDTO, LocationUpdateDTO

router = APIRouter(prefix="/locations", tags=["locations"])

_CACHE_CONTROL_MAX_AGE = "max-age=300"

_location_service: LocationService | None = None


def init_router(location_service: LocationService) -> None:
    global _location_service
    _location_service = location_service


@router.post(
    "/", response_model=LocationDTO, status_code=201, dependencies=[Depends(require_permission("locations:write"))]
)
def create_location(dto: LocationDTO) -> LocationDTO:
    location = LocationApiMapper.to_domain(dto)
    created = _location_service.create(location)
    return LocationApiMapper.to_dto(created)


@router.get("/search", response_model=list[LocationDTO], dependencies=[Depends(require_permission("locations:read"))])
def search_locations(q: str = "", response: Response = None) -> list[LocationDTO]:
    locations = _location_service.search_by_name(q)
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    return [LocationApiMapper.to_dto(loc) for loc in locations]


@router.get("/{location_id}", response_model=LocationDTO, dependencies=[Depends(require_permission("locations:read"))])
def get_location(location_id: str) -> LocationDTO:
    try:
        location = _location_service.get(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LocationApiMapper.to_dto(location)


@router.get("/", response_model=list[LocationDTO], dependencies=[Depends(require_permission("locations:read"))])
def list_locations(
    location_type: str | None = None, parent_id: str | None = None, response: Response = None
) -> list[LocationDTO]:
    if location_type:
        locations = _location_service.list_by_type(location_type)
    elif parent_id:
        locations = _location_service.list_children(parent_id)
    else:
        locations = _location_service.list_all()
    response.headers["Cache-Control"] = _CACHE_CONTROL_MAX_AGE
    return [LocationApiMapper.to_dto(loc) for loc in locations]


@router.put("/{location_id}", response_model=LocationDTO, dependencies=[Depends(require_permission("locations:write"))])
def update_location(location_id: str, dto: LocationUpdateDTO) -> LocationDTO:
    try:
        existing = _location_service.get(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    merged = LocationApiMapper.update_to_domain(dto, existing)
    updated = _location_service.update(location_id, merged)
    return LocationApiMapper.to_dto(updated)


@router.delete("/{location_id}", status_code=204, dependencies=[Depends(require_permission("locations:delete"))])
def delete_location(location_id: str) -> None:
    try:
        _location_service.delete(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
