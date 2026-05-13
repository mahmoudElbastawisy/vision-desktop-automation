"""Screenshot annotation helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from desktop_grounding.logging_config import get_logger
from desktop_grounding.utils.paths import get_screenshot_directories


if TYPE_CHECKING:
    from PIL import Image


logger = get_logger(__name__)


def save_annotated_detection(
    screenshot: Image.Image,
    bbox: tuple[int, int, int, int],
    center: tuple[int, int],
    label: str,
    confidence: float,
    method: str,
    filename_prefix: str = "detection",
) -> Path:
    """Save an annotated copy of a screenshot with a detection overlay."""
    from PIL import ImageDraw, ImageFont

    annotated = screenshot.copy()
    draw = ImageDraw.Draw(annotated)

    x1, y1, x2, y2 = bbox
    center_x, center_y = center
    box_color = (0, 220, 80)
    text_color = (255, 255, 255)
    text_background = (0, 80, 40)
    center_color = (255, 60, 60)

    draw.rectangle((x1, y1, x2, y2), outline=box_color, width=3)
    draw.ellipse((center_x - 4, center_y - 4, center_x + 4, center_y + 4), fill=center_color)

    font = ImageFont.load_default()
    text = f"{label} | {method} | {confidence:.2f}"
    text_bbox = draw.textbbox((x1, y1), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = max(0, x1)
    text_y = max(0, y1 - text_height - 6)

    draw.rectangle(
        (text_x, text_y, text_x + text_width + 8, text_y + text_height + 6),
        fill=text_background,
    )
    draw.text((text_x + 4, text_y + 3), text, fill=text_color, font=font)

    _, annotated_directory = get_screenshot_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = annotated_directory / f"{filename_prefix}_{timestamp}.png"

    try:
        annotated.save(output_path)
    except OSError as exc:
        logger.error("Failed to save annotated screenshot: %s", exc)
        raise

    logger.info("Annotated detection saved: %s", output_path)
    return output_path
