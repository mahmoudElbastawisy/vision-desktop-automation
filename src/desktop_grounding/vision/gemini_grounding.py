"""Optional Gemini-based visual grounding for desktop icons."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Any

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


if TYPE_CHECKING:
    from PIL import Image


logger = get_logger(__name__)

VALID_QUARTERS = {
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "center",
    "unknown",
}


@dataclass(frozen=True)
class GeminiGroundingMatch:
    """A desktop icon candidate located by Gemini."""

    bbox: tuple[int, int, int, int]
    center_x: int
    center_y: int
    confidence: float
    quarter: str
    method: str = "gemini"


def _image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _parse_json_response(text: str) -> dict[str, Any] | None:
    cleaned = _strip_json_fences(text)
    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        logger.error("Gemini response did not contain a JSON object")
        return None

    try:
        payload = json.loads(cleaned[start_index : end_index + 1])
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON: %s", exc)
        return None

    if not isinstance(payload, dict):
        logger.error("Gemini returned JSON that was not an object")
        return None

    return payload


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", "")
    if isinstance(text, str):
        return text
    return str(text)


def _call_gemini(client: Any, image: Image.Image, prompt: str) -> dict[str, Any] | None:
    try:
        from google.genai import types

        image_part = types.Part.from_bytes(data=_image_to_png_bytes(image), mime_type="image/png")
        response = client.models.generate_content(
            model=config.GEMINI_MODEL_NAME,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        return None

    return _parse_json_response(_extract_response_text(response))


def _quarter_crop_box(width: int, height: int, quarter: str) -> tuple[int, int, int, int] | None:
    half_width = width // 2
    half_height = height // 2
    quarter_boxes = {
        "top_left": (0, 0, half_width, half_height),
        "top_right": (half_width, 0, width, half_height),
        "bottom_left": (0, half_height, half_width, height),
        "bottom_right": (half_width, half_height, width, height),
        "center": (width // 4, height // 4, (width * 3) // 4, (height * 3) // 4),
    }
    return quarter_boxes.get(quarter)


def _coerce_number_list(value: Any, expected_length: int, field_name: str) -> list[int] | None:
    if not isinstance(value, list) or len(value) != expected_length:
        logger.error("Gemini %s must be a list of %d numbers", field_name, expected_length)
        return None

    numbers: list[int] = []
    for item in value:
        if not isinstance(item, (int, float)):
            logger.error("Gemini %s contains a non-numeric value: %r", field_name, item)
            return None
        numbers.append(int(round(item)))

    return numbers


def _scale_from_normalized_coordinate(value: int, size: int) -> int:
    return max(0, min(size - 1, round((value / 1000) * size)))


def _scale_bbox_from_normalized(
    bbox: list[int],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1 = _scale_from_normalized_coordinate(bbox[0], width)
    y1 = _scale_from_normalized_coordinate(bbox[1], height)
    x2 = _scale_from_normalized_coordinate(bbox[2], width)
    y2 = _scale_from_normalized_coordinate(bbox[3], height)
    return x1, y1, x2, y2


def _scale_center_from_normalized(center: list[int], width: int, height: int) -> tuple[int, int]:
    return (
        _scale_from_normalized_coordinate(center[0], width),
        _scale_from_normalized_coordinate(center[1], height),
    )


def _is_valid_full_screen_match(
    bbox: tuple[int, int, int, int],
    center: tuple[int, int],
    width: int,
    height: int,
) -> bool:
    x1, y1, x2, y2 = bbox
    center_x, center_y = center
    return (
        0 <= x1 < x2 <= width
        and 0 <= y1 < y2 <= height
        and 0 <= center_x < width
        and 0 <= center_y < height
    )


def find_gemini_icon_match(
    screenshot: Image.Image,
    target_name: str = "Notepad",
) -> GeminiGroundingMatch | None:
    """Locate an icon using a two-step Gemini vision prompt."""
    if not config.ENABLE_GEMINI_GROUNDING:
        logger.info("Gemini grounding is disabled")
        return None

    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY is missing; Gemini grounding will be skipped")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            http_options=types.HttpOptions(
                timeout=int(config.GEMINI_TIMEOUT_SECONDS * 1000),
                retry_options=types.HttpRetryOptions(attempts=config.GEMINI_RETRY_ATTEMPTS),
            )
        )
    except Exception as exc:
        logger.error("Gemini client could not be initialized: %s", exc)
        return None

    quarter_prompt = f"""
You are locating a Windows desktop shortcut.
Target: {target_name}

Look for the Windows 10 Notepad desktop shortcut. It usually appears as a small light-blue
notepad or paper icon, often with lines on the page, and the text label "Notepad" underneath it.
Use both clues:
- the visual Notepad icon
- the readable desktop label text "Notepad"

Decide which screen region contains the shortcut. If you are not sure, use "unknown".
Return only this JSON object, with confidence as a number from 0.0 to 1.0:
{{"quarter":"top_left|top_right|bottom_left|bottom_right|center|unknown","confidence":0.0}}
""".strip()
    quarter_payload = _call_gemini(client, screenshot, quarter_prompt)
    if quarter_payload is None:
        return None

    quarter = str(quarter_payload.get("quarter", "unknown")).strip().lower()
    confidence = quarter_payload.get("confidence", 0.0)
    if quarter not in VALID_QUARTERS:
        logger.error("Gemini returned invalid quarter: %s", quarter)
        return None
    if quarter == "unknown":
        logger.info("Gemini could not identify a likely screen area for %s", target_name)
        return None
    if not isinstance(confidence, int | float):
        logger.error("Gemini quarter confidence was not numeric")
        return None

    crop_box = _quarter_crop_box(screenshot.width, screenshot.height, quarter)
    if crop_box is None:
        return None

    crop = screenshot.crop(crop_box)
    crop_prompt = f"""
You are locating a clickable Windows desktop shortcut inside this crop.
Target: {target_name}

Find the Windows 10 Notepad shortcut. It may be identified by:
- a light-blue Notepad/paper icon with page lines
- the desktop label text "Notepad" underneath the icon

Return a bounding box around the whole clickable shortcut item: include the icon and the
"Notepad" label when visible. Return the center of that whole clickable shortcut item, because
that is where a mouse double-click should land.

Do not choose Notepad++ or any other editor. Only choose the standard Windows Notepad shortcut.
Use normalized coordinates on a 0-1000 scale relative to this crop:
- x=0 is the left edge of the crop
- y=0 is the top edge of the crop
- x=1000 is the right edge of the crop
- y=1000 is the bottom edge of the crop

Return only this JSON object, with confidence as a number from 0.0 to 1.0:
{{"found":true,"bbox":[x1,y1,x2,y2],"center":[x,y],"confidence":0.0}}
If you cannot find it, return:
{{"found":false,"bbox":[0,0,0,0],"center":[0,0],"confidence":0.0}}
""".strip()
    location_payload = _call_gemini(client, crop, crop_prompt)
    if location_payload is None:
        return None

    if location_payload.get("found") is not True:
        logger.info("Gemini did not find %s in the selected crop", target_name)
        return None

    bbox_values = _coerce_number_list(location_payload.get("bbox"), 4, "bbox")
    center_values = _coerce_number_list(location_payload.get("center"), 2, "center")
    location_confidence = location_payload.get("confidence", 0.0)
    if bbox_values is None or center_values is None:
        return None
    if not isinstance(location_confidence, (int, float)):
        logger.error("Gemini location confidence was not numeric")
        return None

    confidence_value = float(location_confidence)
    if confidence_value < config.GEMINI_CONFIDENCE_THRESHOLD:
        logger.info(
            "Gemini confidence %.2f is below threshold %.2f. Raw response: %s",
            confidence_value,
            config.GEMINI_CONFIDENCE_THRESHOLD,
            location_payload,
        )
        return None

    if any(value < 0 or value > 1000 for value in [*bbox_values, *center_values]):
        logger.error("Gemini normalized coordinates must be between 0 and 1000")
        return None

    crop_bbox = _scale_bbox_from_normalized(bbox_values, crop.width, crop.height)
    crop_center = _scale_center_from_normalized(center_values, crop.width, crop.height)

    crop_left, crop_top, _, _ = crop_box
    full_bbox = (
        crop_bbox[0] + crop_left,
        crop_bbox[1] + crop_top,
        crop_bbox[2] + crop_left,
        crop_bbox[3] + crop_top,
    )
    full_center = (crop_center[0] + crop_left, crop_center[1] + crop_top)

    if not _is_valid_full_screen_match(full_bbox, full_center, screenshot.width, screenshot.height):
        logger.error("Gemini returned coordinates outside screenshot bounds")
        return None

    logger.info("Gemini found %s in %s with confidence %.2f", target_name, quarter, confidence_value)
    return GeminiGroundingMatch(
        bbox=full_bbox,
        center_x=full_center[0],
        center_y=full_center[1],
        confidence=confidence_value,
        quarter=quarter,
    )
