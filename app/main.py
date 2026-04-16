from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health, ingest, review
from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agentic Legal Review API",
        description="Agentic document review and case preparation system",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(ingest.router, prefix=settings.api_prefix)
    app.include_router(review.router, prefix=settings.api_prefix)
    return app


app = create_app()
