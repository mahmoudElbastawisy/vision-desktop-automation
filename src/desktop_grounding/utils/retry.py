"""Reusable retry utilities."""

from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import ParamSpec, TypeVar

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


P = ParamSpec("P")
R = TypeVar("R")

logger = get_logger(__name__)


def retry(
    attempts: int = config.MAX_RETRIES,
    delay_seconds: float = config.RETRY_DELAY_SECONDS,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a function when configured exceptions are raised."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None

            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc

                    if attempt == attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            attempts,
                            exc,
                        )
                        break

                    logger.warning(
                        "%s failed on attempt %d/%d: %s. Retrying in %.1f seconds",
                        func.__name__,
                        attempt,
                        attempts,
                        exc,
                        delay_seconds,
                    )
                    sleep(delay_seconds)

            if last_error is None:
                raise RuntimeError("retry wrapper exited without a result or exception")

            raise last_error

        return wrapper

    return decorator
