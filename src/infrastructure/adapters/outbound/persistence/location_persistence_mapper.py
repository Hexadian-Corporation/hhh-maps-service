from src.domain.models.location import Coordinates, Location


class LocationPersistenceMapper:
    @staticmethod
    def to_document(location: Location) -> dict:
        doc = {
            "name": location.name,
            "location_type": location.location_type,
            "parent_id": location.parent_id,
            "coordinates": {
                "x": location.coordinates.x,
                "y": location.coordinates.y,
                "z": location.coordinates.z,
            },
            "has_trade_terminal": location.has_trade_terminal,
            "has_landing_pad": location.has_landing_pad,
            "landing_pad_size": location.landing_pad_size,
        }
        return doc

    @staticmethod
    def to_domain(doc: dict) -> Location:
        coords = doc.get("coordinates", {})
        return Location(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            location_type=doc.get("location_type", ""),
            parent_id=doc.get("parent_id"),
            coordinates=Coordinates(
                x=coords.get("x", 0.0),
                y=coords.get("y", 0.0),
                z=coords.get("z", 0.0),
            ),
            has_trade_terminal=doc.get("has_trade_terminal", False),
            has_landing_pad=doc.get("has_landing_pad", False),
            landing_pad_size=doc.get("landing_pad_size"),
        )
