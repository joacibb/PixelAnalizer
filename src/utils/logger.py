"""
logger.py
---------
Centralised logging configuration for PixelAnalizer.
Call setup_logging() once at application startup.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_DIR = Path(__file__).parents[2] / "logs"
_LOG_FILE = _LOG_DIR / "pixelanalizer.log"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with console and rotating file handlers.

    Parameters
    ----------
    level:
        Minimum log level for both handlers (default: ``logging.INFO``).
        Use ``logging.DEBUG`` for verbose output during development.
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    logging.getLogger(__name__).info(
        "Logging initialised — file: %s", _LOG_FILE
    )
