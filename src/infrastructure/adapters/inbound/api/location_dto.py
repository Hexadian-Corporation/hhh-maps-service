from pydantic import BaseModel, Field


class CoordinatesDTO(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class LocationDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    name: str
    location_type: str
    parent_id: str | None = None
    coordinates: CoordinatesDTO = Field(default_factory=CoordinatesDTO)
    has_trade_terminal: bool = False
    has_landing_pad: bool = False
    landing_pad_size: str | None = None

    model_config = {"populate_by_name": True}


class LocationUpdateDTO(BaseModel):
    name: str | None = None
    location_type: str | None = None
    parent_id: str | None = None
    coordinates: CoordinatesDTO | None = None
    has_trade_terminal: bool | None = None
    has_landing_pad: bool | None = None
    landing_pad_size: str | None = None
