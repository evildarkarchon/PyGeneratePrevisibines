from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger


def setup_logger(log_file: Path | None = None, verbose: bool = False) -> Logger:
    logger.remove()

    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    simple_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"

    logger.add(
        sys.stderr,
        format=simple_format if not verbose else log_format,
        level="DEBUG" if verbose else "INFO",
        colorize=True,
    )

    if log_file:
        logger.add(
            log_file,
            format=log_format,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )

    return logger


def get_logger(name: str) -> Logger:
    return logger.bind(name=name)
