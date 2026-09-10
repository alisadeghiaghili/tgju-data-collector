# -*- coding: utf-8 -*-
"""Logging helpers for the collector package."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO", name: str = "tgju_collector") -> logging.Logger:
    """Configure a process logger with console and optional rotating file output.

    Args:
        level: Logging level name (``DEBUG``, ``INFO``, ...).
        name: Logger name.

    Returns:
        logging.Logger: Configured logger instance.

    Examples:
        >>> log = setup_logging("WARNING")
        >>> log.name
        'tgju_collector'
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger
