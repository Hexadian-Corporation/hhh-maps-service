class LocationNotFoundError(Exception):
    def __init__(self, location_id: str) -> None:
        super().__init__(f"Location not found: {location_id}")
        self.location_id = location_id
