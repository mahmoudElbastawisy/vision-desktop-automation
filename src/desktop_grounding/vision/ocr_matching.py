"""OCR-based desktop label matching."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


if TYPE_CHECKING:
    from PIL import Image


logger = get_logger(__name__)


@dataclass(frozen=True)
class OCRMatch:
    """A candidate detected from OCR text."""

    bbox: tuple[int, int, int, int]
    center_x: int
    center_y: int
    confidence: float
    text: str
    method: str = "ocr"


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _is_text_match(candidate: str, target: str) -> bool:
    normalized_candidate = _normalize_text(candidate)
    normalized_target = _normalize_text(target)

    if normalized_candidate == normalized_target:
        return True

    if normalized_candidate == f"{normalized_target}++":
        return False

    return normalized_target in normalized_candidate


def _text_priority(candidate: str, target: str) -> int:
    normalized_candidate = _normalize_text(candidate)
    normalized_target = _normalize_text(target)

    if normalized_candidate == normalized_target:
        return 2
    if normalized_candidate == f"{normalized_target}++":
        return 0
    if normalized_target in normalized_candidate:
        return 1
    return 0


def _polygon_to_bbox(points: list[list[float]] | tuple[tuple[float, float], ...]) -> tuple[int, int, int, int]:
    x_values = [int(point[0]) for point in points]
    y_values = [int(point[1]) for point in points]
    return min(x_values), min(y_values), max(x_values), max(y_values)


@lru_cache(maxsize=1)
def _get_easyocr_reader() -> Any | None:
    try:
        import easyocr

        return easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception as exc:
        logger.warning("EasyOCR is unavailable; OCR matching will be skipped: %s", exc)
        return None


def find_ocr_matches(
    screenshot: Image.Image,
    target_text: str = "Notepad",
    threshold: float | None = None,
) -> list[OCRMatch]:
    """Find desktop label candidates using EasyOCR."""
    confidence_threshold = threshold if threshold is not None else config.OCR_MATCH_CONFIDENCE_THRESHOLD
    reader = _get_easyocr_reader()

    if reader is None:
        return []

    try:
        import numpy as np

        image_array = np.array(screenshot.convert("RGB"))
        raw_results = reader.readtext(image_array)
    except Exception as exc:
        logger.error("OCR matching failed: %s", exc)
        return []

    matches: list[OCRMatch] = []
    for result in raw_results:
        if len(result) < 3:
            continue

        polygon, text, confidence = result[0], str(result[1]), float(result[2])

        if confidence < confidence_threshold or not _is_text_match(text, target_text):
            continue

        try:
            bbox = _polygon_to_bbox(polygon)
        except (TypeError, ValueError, IndexError) as exc:
            logger.warning("Skipping OCR result with invalid bounding box: %s", exc)
            continue
        matches.append(
            OCRMatch(
                bbox=bbox,
                center_x=(bbox[0] + bbox[2]) // 2,
                center_y=(bbox[1] + bbox[3]) // 2,
                confidence=confidence,
                text=text,
            )
        )

    matches.sort(
        key=lambda match: (_text_priority(match.text, target_text), match.confidence),
        reverse=True,
    )
    logger.info("OCR matching found %d candidates for %r", len(matches), target_text)
    return matches
