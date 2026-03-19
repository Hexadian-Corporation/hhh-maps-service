from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from hexadian_auth_common.fastapi import JWTAuthDependency, _stub_jwt_auth, register_exception_handlers
from opyoid import Injector

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.application.ports.inbound.location_service import LocationService
from src.infrastructure.adapters.inbound.api.location_distance_router import distance_router, init_distance_router
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings
from src.seed import seed_locations


def create_app() -> FastAPI:
    settings = Settings()
    injector = Injector([AppModule(settings)])

    location_service = injector.inject(LocationService)
    init_router(location_service)

    distance_service = injector.inject(LocationDistanceService)
    init_distance_router(distance_service)

    jwt_auth = injector.inject(JWTAuthDependency)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        seed_locations(location_service)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth

    app.include_router(router)
    app.include_router(distance_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8003, reload=True)
