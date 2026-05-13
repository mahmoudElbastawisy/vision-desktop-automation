"""Path helpers for desktop output and screenshots."""

from pathlib import Path

from desktop_grounding import config


def get_desktop_path() -> Path:
    """Return the current user's Desktop path."""
    return Path.home() / "Desktop"


def get_output_directory() -> Path:
    """Create and return the project output directory on the Desktop."""
    output_directory = get_desktop_path() / config.OUTPUT_FOLDER_NAME
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def get_screenshot_directories() -> tuple[Path, Path]:
    """Create and return raw and annotated screenshot directories."""
    screenshots_root = config.PROJECT_ROOT / config.SCREENSHOTS_FOLDER_NAME
    raw_directory = screenshots_root / config.RAW_SCREENSHOTS_FOLDER_NAME
    annotated_directory = screenshots_root / config.ANNOTATED_SCREENSHOTS_FOLDER_NAME

    raw_directory.mkdir(parents=True, exist_ok=True)
    annotated_directory.mkdir(parents=True, exist_ok=True)

    return raw_directory, annotated_directory


def build_post_filename(post_id: int) -> Path:
    """Return the output path for a post text file."""
    if post_id <= 0:
        raise ValueError("post_id must be a positive integer")

    return get_output_directory() / f"post_{post_id}.txt"
