from src.domain.models.location import Location


class LocationPersistenceMapper:
    @staticmethod
    def to_document(location: Location) -> dict:
        doc = {
            "name": location.name,
            "location_type": location.location_type,
            "parent_id": location.parent_id,
            "has_trade_terminal": location.has_trade_terminal,
            "has_landing_pad": location.has_landing_pad,
            "landing_pad_size": location.landing_pad_size,
        }
        return doc

    @staticmethod
    def to_domain(doc: dict) -> Location:
        return Location(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            location_type=doc.get("location_type", ""),
            parent_id=doc.get("parent_id"),
            has_trade_terminal=doc.get("has_trade_terminal", False),
            has_landing_pad=doc.get("has_landing_pad", False),
            landing_pad_size=doc.get("landing_pad_size"),
        )
