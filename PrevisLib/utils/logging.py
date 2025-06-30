from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path

    from loguru import Logger


def setup_logger(log_file: Path | None = None, verbose: bool = False) -> Logger:
    """
    Configures and sets up the logger with specified formatting, verbosity, and file
    logging options. It resets any existing logger configurations and applies new
    settings based on the provided parameters. The function allows setting a file
    log target, controlling verbosity in the console, and defining rotation and
    retention policies for file logs. A logger instance is returned after setup.

    :param log_file: Optional path to the log file. When provided, log messages are
                     written to this file with additional settings like size-based
                     rotation and compression. If None, file logging is not enabled.
    :type log_file: Path | None
    :param verbose: Boolean flag indicating whether detailed log formatting and
                    DEBUG level logging should be enabled to provide more
                    comprehensive information. Set to True for verbose output.
    :type verbose: bool
    :return: Configured logger instance that can be used to log messages based on
             the setup parameters.
    :rtype: Logger
    """
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
