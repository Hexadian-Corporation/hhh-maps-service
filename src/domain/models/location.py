from dataclasses import dataclass, field


@dataclass
class Coordinates:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Location:
    id: str | None = None
    name: str = ""
    location_type: str = ""  # system, planet, moon, station, city, outpost
    parent_id: str | None = None
    coordinates: Coordinates = field(default_factory=Coordinates)
    has_trade_terminal: bool = False
    has_landing_pad: bool = False
    landing_pad_size: str | None = None  # small, medium, large, extra_large
