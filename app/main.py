from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, ingest, review, review_runs
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.observability import setup_phoenix
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    setup_phoenix()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agentic Legal Review API",
        description="Agentic document review and case preparation system",
        version="0.4.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(ingest.router, prefix=settings.api_prefix)
    app.include_router(review.router, prefix=settings.api_prefix)
    app.include_router(review_runs.router, prefix=settings.api_prefix)
    return app


app = create_app()
