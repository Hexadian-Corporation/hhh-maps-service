from pydantic import BaseModel, Field


class LocationDistanceDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    from_location_id: str
    to_location_id: str
    distance: float
    travel_type: str  # quantum | scm | on_foot
    in_game: bool = True

    model_config = {"populate_by_name": True}


class LocationDistanceCreateDTO(BaseModel):
    from_location_id: str
    to_location_id: str
    distance: float
    travel_type: str  # quantum | scm | on_foot
    in_game: bool = True


class LocationDistanceUpdateDTO(BaseModel):
    from_location_id: str | None = None
    to_location_id: str | None = None
    distance: float | None = None
    travel_type: str | None = None
    in_game: bool | None = None
