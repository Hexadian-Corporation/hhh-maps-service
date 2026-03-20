from dataclasses import dataclass


@dataclass
class LocationDistance:
    id: str | None = None
    from_location_id: str = ""  # Reference to Location.id (origin)
    to_location_id: str = ""  # Reference to Location.id (destination)
    distance: float = 0.0  # Distance in meters
    travel_type: str = ""  # quantum | scm | on_foot
    in_game: bool = True
