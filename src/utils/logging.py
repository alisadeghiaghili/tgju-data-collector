# -*- coding: utf-8 -*-
"""Logging configuration for TGJU Data Collector."""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(name: str = 'tgju', log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging with both file and console handlers.

    Args:
        name: Logger name
        log_level: Minimum log level

    Returns:
        Configured logger instance
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # File handler - logs everything
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"{name}_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - logs INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)-8s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
