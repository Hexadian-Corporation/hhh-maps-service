from src.domain.models.location_distance import LocationDistance


class LocationDistancePersistenceMapper:
    @staticmethod
    def to_document(distance: LocationDistance) -> dict:
        return {
            "from_location_id": distance.from_location_id,
            "to_location_id": distance.to_location_id,
            "distance": distance.distance,
            "travel_type": distance.travel_type,
            "in_game": distance.in_game,
        }

    @staticmethod
    def to_domain(doc: dict) -> LocationDistance:
        return LocationDistance(
            id=str(doc["_id"]),
            from_location_id=doc.get("from_location_id", ""),
            to_location_id=doc.get("to_location_id", ""),
            distance=doc.get("distance", 0.0),
            travel_type=doc.get("travel_type", ""),
            in_game=doc.get("in_game", True),
        )
