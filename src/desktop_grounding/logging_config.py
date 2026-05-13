"""Logging helpers for the desktop automation project."""

import logging


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%H:%M:%S"


def _build_handler() -> logging.Handler:
    """Create a console handler, using rich formatting when available."""
    try:
        from rich.logging import RichHandler

        return RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=False,
            show_time=False
        )
    except ImportError:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        return handler


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for console output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    handler = _build_handler()
    handler.setLevel(level)

    if handler.formatter is None:
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for a module."""
    configure_logging()
    return logging.getLogger(name)
