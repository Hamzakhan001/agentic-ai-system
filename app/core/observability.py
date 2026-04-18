from __future__ import annotations

import os

from opentelemetry import trace

from app.core.config import get_settings
from app.core.logging import logger


_phoenix_initialized = False


def setup_phoenix() -> None:
    global _phoenix_initialized
    if _phoenix_initialized:
        return

    settings = get_settings()
    if not settings.phoenix_enabled:
        logger.info("phoenix_disabled")
        return

    collector_endpoint = settings.phoenix_collector_endpoint.rstrip("/")
    http_traces_endpoint = collector_endpoint
    if not http_traces_endpoint.endswith("/v1/traces"):
        http_traces_endpoint = f"{collector_endpoint}/v1/traces"

    os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", collector_endpoint)
    os.environ.setdefault("PHOENIX_PROJECT_NAME", settings.phoenix_project_name)
    if settings.phoenix_api_key:
        os.environ.setdefault("PHOENIX_API_KEY", settings.phoenix_api_key)

    from phoenix.otel import register
    from openinference.instrumentation.openai import OpenAIInstrumentor

    tracer_provider = register(
        project_name=settings.phoenix_project_name,
        endpoint=http_traces_endpoint,
        protocol="http/protobuf",
        batch=False,
        auto_instrument=True,
    )
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
    _phoenix_initialized = True

    logger.info(
        "phoenix_initialized",
        project_name=settings.phoenix_project_name,
        collector_endpoint=http_traces_endpoint,
    )


def get_tracer(name: str = "agentic-legal-review"):
    return trace.get_tracer(name)
