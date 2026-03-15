from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from opyoid import Injector

from src.application.ports.inbound.location_service import LocationService
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings
from src.seed import seed_locations


def create_app() -> FastAPI:
    settings = Settings()
    injector = Injector([AppModule(settings)])

    location_service = injector.inject(LocationService)
    init_router(location_service)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        seed_locations(location_service)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8003, reload=True)
