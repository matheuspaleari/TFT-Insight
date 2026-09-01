from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.integration_engine.api.heavy_request_middleware import (
    HeavyRequestQueueMiddleware,
)
from src.integration_engine.api.routes import (
    analysis_router,
    benchmark_router,
    health_router,
    integrated_analysis_router,
)
from src.integration_engine.api.routes.queue_status import (
    router as queue_status_router,
)
from src.integration_engine.api.routes.post_match import (
    router as post_match_router,
)
from src.integration_engine.api.routes.composition_intelligence import (
    router as composition_intelligence_router,
)
from src.integration_engine.api.routes.contest_intelligence import (
    router as contest_intelligence_router,
)
from src.integration_engine.api.routes.economy_intelligence import (
    router as economy_intelligence_router,
)
from src.integration_engine.api.routes.carry_item_intelligence import (
    router as carry_item_intelligence_router,
)
from src.integration_engine.config import (
    IntegrationSettings,
)
from src.partner_analytics import (
    PartnerAnalyticsMiddleware,
)


def create_app() -> FastAPI:
    settings = (
        IntegrationSettings.from_environment()
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        description=(
            "API de inteligência explicável para TFT. "
            "Projetada para integração B2B, SDKs e produtos parceiros."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
        ],
    )

    app.add_middleware(
        PartnerAnalyticsMiddleware
    )

    app.add_middleware(
        HeavyRequestQueueMiddleware
    )

    @app.get(
        "/",
        tags=["system"],
    )
    def root() -> dict:
        return {
            "service": settings.app_name,
            "status": "online",
            "api_version": settings.api_version,
            "documentation": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
        }

    app.include_router(
        health_router
    )
    app.include_router(
        queue_status_router
    )
    app.include_router(
        analysis_router
    )
    app.include_router(
        integrated_analysis_router
    )
    app.include_router(
        benchmark_router
    )
    app.include_router(
        post_match_router
    )
    app.include_router(
        composition_intelligence_router
    )
    app.include_router(
        contest_intelligence_router
    )
    app.include_router(
        economy_intelligence_router
    )
    app.include_router(
        carry_item_intelligence_router
    )

    return app


app = create_app()