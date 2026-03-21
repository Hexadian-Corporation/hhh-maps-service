from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "hhh-maps-service"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "hhh_maps"
    host: str = "0.0.0.0"
    port: int = 8003
    jwt_secret: str = Field(default="change-me-in-production", validation_alias="HEXADIAN_AUTH_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    cache_ttl_seconds: int = 300
    location_cache_maxsize: int = 256
    distance_cache_maxsize: int = 512

    model_config = {"env_prefix": "HHH_MAPS_"}
