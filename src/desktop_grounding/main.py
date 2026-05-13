"""Final orchestration for the desktop grounding automation workflow."""

from dataclasses import dataclass

from desktop_grounding.api.posts_client import Post, fetch_posts
from desktop_grounding.automation.notepad_controller import (
    close_notepad,
    format_post_content,
    launch_notepad_from_desktop,
    save_notepad_file,
    write_content_to_notepad,
)
from desktop_grounding.logging_config import get_logger
from desktop_grounding.utils.paths import build_post_filename, get_output_directory


logger = get_logger(__name__)


@dataclass(frozen=True)
class WorkflowSummary:
    """Summary of one automation run."""

    total_posts: int
    successful_saves: int
    failures: int


def _process_post(post: Post) -> bool:
    """Write one post to Notepad and save it through the UI."""
    logger.info("Processing post %d: %s", post.id, post.title)

    if not launch_notepad_from_desktop():
        logger.error("Skipping post %d because Notepad could not be launched", post.id)
        return False

    try:
        content = format_post_content(post.title, post.body)
        target_file = build_post_filename(post.id)

        write_content_to_notepad(content)
        save_notepad_file(target_file)
        logger.info("Saved post %d to %s", post.id, target_file)
        return True
    finally:
        try:
            close_notepad()
        except Exception as exc:
            logger.warning("Failed to close Notepad cleanly: %s", exc)


def run_workflow() -> WorkflowSummary:
    """Run the full posts-to-Notepad workflow."""
    logger.info("Starting desktop grounding automation workflow")
    output_directory = get_output_directory()
    logger.info("Output directory ready: %s", output_directory)

    posts = fetch_posts()
    if not posts:
        logger.error("No posts were fetched; workflow cannot continue")
        return WorkflowSummary(total_posts=0, successful_saves=0, failures=0)

    successful_saves = 0
    failures = 0

    for post in posts:
        try:
            if _process_post(post):
                successful_saves += 1
            else:
                failures += 1
        except Exception as exc:
            failures += 1
            logger.exception("Failed to process post %d: %s", post.id, exc)

    logger.info("Desktop grounding automation workflow completed")        

    return WorkflowSummary(
        total_posts=len(posts),
        successful_saves=successful_saves,
        failures=failures,
    )


def main() -> int:
    """Application entry point."""
    summary = run_workflow()

    logger.info(
        "Workflow summary: total posts fetched=%d, successful saves=%d, failures=%d",
        summary.total_posts,
        summary.successful_saves,
        summary.failures,
    )

    if summary.total_posts == 0 or summary.successful_saves == 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
