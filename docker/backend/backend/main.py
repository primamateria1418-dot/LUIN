"""
LUIN FastAPI Application — Executive Marketing Engine
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import async_session_maker, seed_initial_clients
from backend.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("luin")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LUIN Engine starting up...")
    async with async_session_maker() as session:
        await seed_initial_clients(session)
    yield
    logger.info("LUIN Engine shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.routes import auth, assistant, billing, campaigns, tahuti_webhook, generate, workspaces, client_control, campaign_studio
    from backend.modules import brand_pack

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(assistant.router, prefix="/api/v1", tags=["assistant"])
    app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
    app.include_router(campaigns.router, prefix="/api/v1", tags=["campaigns"])
    app.include_router(tahuti_webhook.router, prefix="/api/v1", tags=["crm"])
    app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
    app.include_router(workspaces.router, prefix="/api/v1", tags=["workspaces"])
    app.include_router(brand_pack.router, prefix="/api/v1", tags=["brand-pack"])
    app.include_router(client_control.router, prefix="/api/v1", tags=["client-control"])
    app.include_router(campaign_studio.router, prefix="/api/v1", tags=["campaign-studio"])

    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()
