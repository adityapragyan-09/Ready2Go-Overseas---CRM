"""
Ready2Go CRM — Centralized Logging Configuration

Configures the standard library logging module for the entire application.
Exposes a single logger instance to be used across all modules.

Usage:
    from app.core.logging import logger
    logger.info("This is an info message")
    logger.error("An error occurred")
"""

import logging
import sys

from app.core.config import settings

# Define logging format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Configure root logger or create app logger
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# App-wide logger instance
logger = logging.getLogger("ready2go_crm")
