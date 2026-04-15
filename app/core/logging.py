from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import get_settings


_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

    _configured = True


logger = structlog.get_logger()
