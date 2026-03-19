from dataclasses import dataclass


@dataclass
class Location:
    id: str | None = None
    name: str = ""
    location_type: str = ""  # system | planet | moon | station | city | outpost | gateway
    parent_id: str | None = None
    has_trade_terminal: bool = False
    has_landing_pad: bool = False
    landing_pad_size: str | None = None  # small | medium | large | extra_large
