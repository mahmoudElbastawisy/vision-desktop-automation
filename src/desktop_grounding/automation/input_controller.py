"""Safe mouse and keyboard helpers built on pyautogui."""

from time import sleep

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


logger = get_logger(__name__)


def _get_pyautogui():
    """Import and configure pyautogui for safe GUI automation."""
    try:
        import pyautogui
    except ImportError as exc:
        logger.error("pyautogui is required for desktop input automation")
        raise RuntimeError("pyautogui is required for desktop input automation") from exc

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = config.GUI_ACTION_DELAY_SECONDS
    return pyautogui


def move_to(x: int, y: int) -> None:
    """Move the mouse pointer to the given screen coordinates."""
    pyautogui = _get_pyautogui()
    logger.info("Moving mouse to (%d, %d)", x, y)
    pyautogui.moveTo(x, y, duration=config.GUI_ACTION_DELAY_SECONDS)


def double_click(x: int, y: int) -> None:
    """Double-click at the given screen coordinates."""
    pyautogui = _get_pyautogui()
    logger.info("Double-clicking at (%d, %d)", x, y)
    pyautogui.moveTo(x, y, duration=config.GUI_ACTION_DELAY_SECONDS)
    pyautogui.doubleClick()
    sleep(config.GUI_ACTION_DELAY_SECONDS)


def type_text(text: str) -> None:
    """Type or paste text into the active window."""
    pyautogui = _get_pyautogui()
    logger.info("Entering text into active window")

    if not text:
        return

    try:
        import pyperclip

        pyperclip.copy(text)
        sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
    except Exception as exc:
        logger.warning("Clipboard paste unavailable; falling back to pyautogui.write: %s", exc)
        pyautogui.write(text, interval=0.01)

    sleep(config.GUI_ACTION_DELAY_SECONDS)


def press_hotkey(*keys: str) -> None:
    """Press a keyboard shortcut."""
    if not keys:
        raise ValueError("at least one key is required")

    pyautogui = _get_pyautogui()
    logger.info("Pressing hotkey: %s", "+".join(keys))
    pyautogui.hotkey(*keys)
    sleep(config.GUI_ACTION_DELAY_SECONDS)


def press_key(key: str) -> None:
    """Press a single keyboard key."""
    if not key:
        raise ValueError("key cannot be empty")

    pyautogui = _get_pyautogui()
    logger.info("Pressing key: %s", key)
    pyautogui.press(key)
    sleep(config.GUI_ACTION_DELAY_SECONDS)
