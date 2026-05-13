"""Window management helpers for Windows desktop automation."""

from time import monotonic, sleep

from desktop_grounding import config
from desktop_grounding.automation.input_controller import press_hotkey
from desktop_grounding.logging_config import get_logger


logger = get_logger(__name__)


def _get_window_titles() -> list[str]:
    try:
        import pygetwindow
    except ImportError:
        logger.warning("pygetwindow is unavailable; window lookup cannot be performed")
        return []

    try:
        return [title for title in pygetwindow.getAllTitles() if title.strip()]
    except Exception as exc:
        logger.error("Failed to read open window titles: %s", exc)
        return []


def wait_for_window(title_contains: str, timeout_seconds: float = 5.0) -> bool:
    """Wait until a window title containing the given text appears."""
    if not title_contains:
        raise ValueError("title_contains cannot be empty")

    expected_title = title_contains.lower()
    deadline = monotonic() + timeout_seconds

    while monotonic() < deadline:
        titles = _get_window_titles()
        if any(expected_title in title.lower() for title in titles):
            logger.info("Window found containing title: %s", title_contains)
            return True

        sleep(config.GUI_ACTION_DELAY_SECONDS)

    logger.warning("Timed out waiting for window containing title: %s", title_contains)
    return False


def close_active_window() -> None:
    """Close the active window using the standard Alt+F4 shortcut."""
    logger.info("Closing active window")
    press_hotkey("alt", "f4")


def show_desktop() -> None:
    """Show the Windows desktop using Win+D."""
    logger.info("Showing desktop")
    press_hotkey("win", "d")
    sleep(config.GUI_ACTION_DELAY_SECONDS)
