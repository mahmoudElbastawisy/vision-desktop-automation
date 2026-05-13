"""Template matching helpers for desktop icon grounding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


if TYPE_CHECKING:
    from PIL import Image


logger = get_logger(__name__)


@dataclass(frozen=True)
class TemplateMatch:
    """A candidate detected by OpenCV template matching."""

    bbox: tuple[int, int, int, int]
    center_x: int
    center_y: int
    confidence: float
    method: str = "template"


def _default_template_path() -> Path:
    return config.TEMPLATES_DIR / "notepad_icon.png"


def find_template_matches(
    screenshot: Image.Image,
    template_path: Path | None = None,
    threshold: float | None = None,
) -> list[TemplateMatch]:
    """Find icon candidates using grayscale OpenCV template matching."""
    resolved_template_path = template_path or _default_template_path()
    confidence_threshold = threshold if threshold is not None else config.ICON_MATCH_CONFIDENCE_THRESHOLD

    if not resolved_template_path.exists():
        logger.info("Template image not found: %s", resolved_template_path)
        return []

    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        logger.error("Template matching requires OpenCV and NumPy: %s", exc)
        return []

    screenshot_array = np.array(screenshot.convert("RGB"))
    screenshot_gray = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2GRAY)
    template_gray = cv2.imread(str(resolved_template_path), cv2.IMREAD_GRAYSCALE)

    if template_gray is None:
        logger.error("Template image could not be read: %s", resolved_template_path)
        return []

    template_height, template_width = template_gray.shape[:2]
    screenshot_height, screenshot_width = screenshot_gray.shape[:2]

    if template_width > screenshot_width or template_height > screenshot_height:
        logger.warning("Template is larger than screenshot; skipping template matching")
        return []

    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    y_coordinates, x_coordinates = np.where(result >= confidence_threshold)

    matches: list[TemplateMatch] = []
    seen_boxes: set[tuple[int, int, int, int]] = set()

    for x, y in zip(x_coordinates, y_coordinates, strict=False):
        confidence = float(result[y, x])
        bbox = (int(x), int(y), int(x + template_width), int(y + template_height))

        if bbox in seen_boxes:
            continue

        seen_boxes.add(bbox)
        matches.append(
            TemplateMatch(
                bbox=bbox,
                center_x=(bbox[0] + bbox[2]) // 2,
                center_y=(bbox[1] + bbox[3]) // 2,
                confidence=confidence,
            )
        )

    matches.sort(key=lambda match: match.confidence, reverse=True)
    logger.info("Template matching found %d candidates", len(matches))
    return matches
