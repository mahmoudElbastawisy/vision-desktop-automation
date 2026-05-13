"""Desktop screenshot capture utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from desktop_grounding.logging_config import get_logger
from desktop_grounding.utils.paths import get_screenshot_directories


if TYPE_CHECKING:
    from PIL import Image


logger = get_logger(__name__)


@dataclass(frozen=True)
class DesktopScreenshot:
    """Captured desktop screenshot and optional saved path."""

    image: Image.Image
    path: Path | None
    width: int
    height: int


class ScreenshotCaptureError(RuntimeError):
    """Raised when the desktop screenshot cannot be captured."""


def capture_desktop_screenshot(save: bool = True) -> DesktopScreenshot:
    """Capture the full primary monitor as a PIL image."""
    try:
        import mss
        from PIL import Image
    except ImportError as exc:
        logger.error("Screenshot capture requires mss and Pillow: %s", exc)
        raise ScreenshotCaptureError("mss and Pillow are required for screenshot capture") from exc

    try:
        with mss.mss() as screen_capture:
            monitor = screen_capture.monitors[1]
            raw_screenshot = screen_capture.grab(monitor)
            image = Image.frombytes("RGB", raw_screenshot.size, raw_screenshot.rgb)
    except Exception as exc:
        logger.error("Failed to capture desktop screenshot: %s", exc)
        raise ScreenshotCaptureError("failed to capture desktop screenshot") from exc

    path: Path | None = None
    if save:
        try:
            raw_directory, _ = get_screenshot_directories()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = raw_directory / f"desktop_{timestamp}.png"
            image.save(path)
            logger.info("Screenshot captured: %s", path)
        except OSError as exc:
            logger.warning("Screenshot captured but could not be saved: %s", exc)
            path = None
    else:
        logger.info("Screenshot captured")

    return DesktopScreenshot(
        image=image,
        path=path,
        width=image.width,
        height=image.height,
    )
