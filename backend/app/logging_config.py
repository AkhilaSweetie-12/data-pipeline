"""Centralized logging configuration."""
import logging
import sys

from app.config import get_settings


def configure_logging() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger("retail_api")
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level.upper())
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
