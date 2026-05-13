"""Notepad automation driven by visually grounded desktop coordinates."""

from pathlib import Path
from time import sleep

from desktop_grounding import config
from desktop_grounding.automation.input_controller import double_click, press_hotkey, press_key, type_text
from desktop_grounding.automation.window_manager import close_active_window, show_desktop, wait_for_window
from desktop_grounding.logging_config import get_logger
from desktop_grounding.vision.grounding import find_desktop_icon


logger = get_logger(__name__)


def launch_notepad_from_desktop() -> bool:
    """Launch Notepad by visually locating and double-clicking its desktop icon."""
    for attempt in range(1, config.MAX_RETRIES + 1):
        logger.info("Launching Notepad from desktop, attempt %d/%d", attempt, config.MAX_RETRIES)
        show_desktop()
        sleep(config.GUI_ACTION_DELAY_SECONDS)

        grounding_result = find_desktop_icon("Notepad", save_debug=True)
        if grounding_result is None:
            logger.error("Notepad desktop icon was not found")
        else:
            double_click(grounding_result.center_x, grounding_result.center_y)
            sleep(config.WINDOW_LAUNCH_DELAY_SECONDS)

            if wait_for_window("Notepad", timeout_seconds=5.0):
                logger.info("Notepad launched successfully")
                return True

            logger.warning("Notepad icon clicked, but Notepad window did not appear")

        if attempt < config.MAX_RETRIES:
            sleep(config.RETRY_DELAY_SECONDS)

    logger.error("Failed to launch Notepad from desktop")
    return False


def write_content_to_notepad(content: str) -> None:
    """Write content into the active Notepad window."""
    logger.info("Writing content to Notepad")
    type_text(content)


def save_notepad_file(file_path: Path) -> None:
    """Save the active Notepad document through the Save dialog."""
    target_path = file_path.expanduser().resolve()
    logger.info("Saving Notepad file to: %s", target_path)

    # Remove existing file first to avoid overwrite confirmation prompts.
    if target_path.exists():
        logger.info("Existing file found, deleting before save: %s", target_path)
        target_path.unlink()

    press_hotkey("ctrl", "s")
    sleep(config.SAVE_DIALOG_DELAY_SECONDS)

    type_text(str(target_path))
    press_key("enter")
    sleep(config.SAVE_DIALOG_DELAY_SECONDS)


def close_notepad() -> None:
    """Close the active Notepad window."""
    logger.info("Closing Notepad")
    close_active_window()
    sleep(config.GUI_ACTION_DELAY_SECONDS)


def format_post_content(title: str, body: str) -> str:
    """Format a post for writing into Notepad."""
    return f"Title: {title}\n\n{body}\n"
