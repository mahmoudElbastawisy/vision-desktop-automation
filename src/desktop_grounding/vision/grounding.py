"""Visual grounding orchestration for desktop icons."""

from dataclasses import dataclass
from pathlib import Path

from desktop_grounding.logging_config import get_logger
from desktop_grounding.vision.annotation import save_annotated_detection
from desktop_grounding.vision.ocr_matching import OCRMatch, find_ocr_matches
from desktop_grounding.vision.screenshot import ScreenshotCaptureError, capture_desktop_screenshot
from desktop_grounding.vision.template_matching import TemplateMatch, find_template_matches


logger = get_logger(__name__)


@dataclass(frozen=True)
class GroundingResult:
    """Final selected desktop icon grounding result."""

    target_name: str
    bbox: tuple[int, int, int, int]
    center_x: int
    center_y: int
    confidence: float
    method_used: str
    debug_image_path: Path | None = None


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _rank_candidate(candidate: OCRMatch | TemplateMatch, target_name: str) -> tuple[float, int, int]:
    exact_text_priority = 0
    method_priority = 1 if candidate.method == "ocr" else 0

    if isinstance(candidate, OCRMatch):
        normalized_candidate = _normalize_text(candidate.text)
        normalized_target = _normalize_text(target_name)
        if normalized_candidate == normalized_target:
            exact_text_priority = 2
        elif normalized_target in normalized_candidate:
            exact_text_priority = 1

    return exact_text_priority, method_priority, candidate.confidence


def find_desktop_icon(
    target_name: str = "Notepad",
    save_debug: bool = True,
) -> GroundingResult | None:
    """Locate a desktop icon visually and return its center coordinates."""
    logger.info("Starting visual grounding for desktop icon: %s", target_name)

    try:
        screenshot = capture_desktop_screenshot(save=save_debug)
    except ScreenshotCaptureError:
        logger.error("Unable to locate %s because screenshot capture failed", target_name)
        return None

    ocr_matches = find_ocr_matches(screenshot.image, target_text=target_name)
    template_matches = find_template_matches(screenshot.image)
    candidates: list[OCRMatch | TemplateMatch] = [*ocr_matches, *template_matches]

    if not candidates:
        logger.info("No visual candidates found for desktop icon: %s", target_name)
        return None

    best_candidate = max(candidates, key=lambda candidate: _rank_candidate(candidate, target_name))
    debug_image_path: Path | None = None

    if save_debug:
        try:
            debug_image_path = save_annotated_detection(
                screenshot=screenshot.image,
                bbox=best_candidate.bbox,
                center=(best_candidate.center_x, best_candidate.center_y),
                label=target_name,
                confidence=best_candidate.confidence,
                method=best_candidate.method,
                filename_prefix=f"{target_name.lower().replace(' ', '_')}_grounding",
            )
        except Exception as exc:
            logger.error("Detection found but debug annotation could not be saved: %s", exc)

    logger.info(
        "Selected %s candidate for %s at (%d, %d) with confidence %.2f",
        best_candidate.method,
        target_name,
        best_candidate.center_x,
        best_candidate.center_y,
        best_candidate.confidence,
    )

    return GroundingResult(
        target_name=target_name,
        bbox=best_candidate.bbox,
        center_x=best_candidate.center_x,
        center_y=best_candidate.center_y,
        confidence=best_candidate.confidence,
        method_used=best_candidate.method,
        debug_image_path=debug_image_path,
    )
