"""
Logger module for the Motor Insurance Analytics project.
Provides centralized logging configuration.
"""

import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")


def setup_logger(name: str = "motor_insurance", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance with file and console handlers.

    Parameters
    ----------
    name : str
        Name of the logger.
    level : int
        Logging level (default: logging.INFO).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_pipeline_step(message: str, logger: logging.Logger = None) -> None:
    """
    Log a pipeline step message.

    Parameters
    ----------
    message : str
        Message to log.
    logger : logging.Logger, optional
        Logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = setup_logger()
    logger.info(f"[PIPELINE] {message}")


def log_error(message: str, logger: logging.Logger = None) -> None:
    """
    Log an error message.

    Parameters
    ----------
    message : str
        Error message to log.
    logger : logging.Logger, optional
        Logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = setup_logger()
    logger.error(f"[ERROR] {message}")
    