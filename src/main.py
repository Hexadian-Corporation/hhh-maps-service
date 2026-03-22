import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from hexadian_auth_common.fastapi import JWTAuthDependency, _stub_jwt_auth, register_exception_handlers
from hhh_events import EventSubscriber
from opyoid import Injector

from src.application.ports.inbound.location_distance_service import LocationDistanceService
from src.application.ports.inbound.location_service import LocationService
from src.application.services.import_handler import DistanceImportHandler, LocationImportHandler
from src.infrastructure.adapters.inbound.api.location_distance_router import distance_router, init_distance_router
from src.infrastructure.adapters.inbound.api.location_router import init_router, router
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings
from src.seed import seed_distances, seed_locations

logger = logging.getLogger(__name__)


async def _run_subscriber(subscriber: EventSubscriber, handler: object, label: str) -> None:
    """Background task that listens for import events."""
    try:
        async for event in subscriber.stream():
            await handler.handle(event)  # type: ignore[union-attr]
    except asyncio.CancelledError:
        logger.info("%s subscriber stopped", label)
    except Exception:
        logger.exception("%s subscriber crashed", label)


def create_app() -> FastAPI:
    settings = Settings()
    module = AppModule(settings)
    injector = Injector([module])

    location_service = injector.inject(LocationService)
    init_router(location_service)

    distance_service = injector.inject(LocationDistanceService)
    init_distance_router(distance_service)

    location_handler = injector.inject(LocationImportHandler)
    distance_handler = injector.inject(DistanceImportHandler)

    jwt_auth = injector.inject(JWTAuthDependency)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await module.create_indexes()
        await seed_locations(location_service)
        await seed_distances(location_service, distance_service)

        location_subscriber = EventSubscriber(
            events_collection=module.events_collection,
            token_collection=module.token_collection,
            subscriber_id="maps-service-locations",
            event_types=["locations.bulk_import"],
        )
        distance_subscriber = EventSubscriber(
            events_collection=module.events_collection,
            token_collection=module.token_collection,
            subscriber_id="maps-service-distances",
            event_types=["distances.bulk_import"],
        )
        tasks = [
            asyncio.create_task(_run_subscriber(location_subscriber, location_handler, "Location")),
            asyncio.create_task(_run_subscriber(distance_subscriber, distance_handler, "Distance")),
        ]
        yield
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        module.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
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
    _settings = Settings()
    uvicorn.run("src.main:app", host=_settings.host, port=_settings.port, reload=True)
