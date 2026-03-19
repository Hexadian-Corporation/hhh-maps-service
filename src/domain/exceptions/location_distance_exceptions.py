class LocationDistanceNotFoundError(Exception):
    def __init__(self, distance_id: str) -> None:
        super().__init__(f"Location distance not found: {distance_id}")
        self.distance_id = distance_id
