"""
Ready2Go CRM — Centralized Logging Configuration

Configures structured enterprise logging for the entire application.
Uses JSON format in production for log aggregation compatibility.

Usage:
    from app.core.logging import logger
    logger.info("Application started", extra={"module": "main"})
    logger.error("An error occurred", exc_info=True)
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        return json.dumps(log_entry)


def setup_logging() -> logging.Logger:
    """Configure and return the application logger with structured formatting."""
    root_logger = logging.getLogger("ready2go_crm")
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.propagate = False

    return root_logger


logger = setup_logging()
