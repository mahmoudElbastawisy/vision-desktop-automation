"""Client for fetching posts from JSONPlaceholder."""

from dataclasses import dataclass
from typing import Any, Self

import requests

from desktop_grounding import config
from desktop_grounding.logging_config import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class Post:
    """Structured representation of a JSONPlaceholder post."""

    user_id: int
    id: int
    title: str
    body: str

    @classmethod
    def from_api_payload(cls, payload: dict[str, Any]) -> Self:
        """Create a Post from a JSONPlaceholder response item."""
        return cls(
            user_id=int(payload["userId"]),
            id=int(payload["id"]),
            title=str(payload["title"]),
            body=str(payload["body"]),
        )


def _fallback_posts(reason: str) -> list[Post]:
    """Return sample posts when the live API is unavailable."""
    logger.warning("Using fallback sample posts because %s", reason)
    return [
        Post(
            user_id=1,
            id=1,
            title="Desktop automation overview",
            body="This sample post demonstrates saving API-style content through Notepad automation.",
        ),
        Post(
            user_id=1,
            id=2,
            title="Visual grounding",
            body="The application locates desktop icons from screenshots instead of relying on fixed coordinates.",
        ),
        Post(
            user_id=1,
            id=3,
            title="Screenshot capture",
            body="Fresh screenshots help the automation adapt when icons move around the desktop.",
        ),
        Post(
            user_id=1,
            id=4,
            title="OCR fallback",
            body="Text labels can help identify desktop shortcuts when template matching is not available.",
        ),
        Post(
            user_id=1,
            id=5,
            title="Template matching",
            body="A stored icon image can provide a second detection strategy for robust grounding.",
        ),
        Post(
            user_id=1,
            id=6,
            title="Safe retries",
            body="Retry logic gives transient desktop and network operations a chance to recover cleanly.",
        ),
        Post(
            user_id=1,
            id=7,
            title="Notepad workflow",
            body="The demo opens Notepad visually, writes content, saves the file, and closes the window.",
        ),
        Post(
            user_id=1,
            id=8,
            title="Output files",
            body="Each post is saved to the Desktop project folder with a predictable post identifier.",
        ),
        Post(
            user_id=1,
            id=9,
            title="Debug artifacts",
            body="Annotated screenshots make it easier to explain and verify the visual detection process.",
        ),
        Post(
            user_id=1,
            id=10,
            title="Graceful degradation",
            body="Fallback data lets the automation demo continue even when the external API is unavailable.",
        ),
    ]


def fetch_posts() -> list[Post]:
    """Fetch the first configured posts from JSONPlaceholder."""
    params = {"_limit": config.POSTS_LIMIT}

    try:
        logger.info("Fetching posts from JSONPlaceholder")
        response = requests.get(
            config.POSTS_API_URL,
            params=params,
            timeout=config.API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        logger.error("API request timed out after %.1f seconds", config.API_TIMEOUT_SECONDS)
        return _fallback_posts("the API request timed out")
    except requests.RequestException as exc:
        logger.error("API request failed: %s", exc)
        return _fallback_posts("the API request failed")
    except ValueError as exc:
        logger.error("API returned invalid JSON: %s", exc)
        return _fallback_posts("the API returned invalid JSON")

    if not isinstance(payload, list):
        logger.error("API returned unexpected payload type: %s", type(payload).__name__)
        return _fallback_posts("the API returned an unexpected payload type")

    posts: list[Post] = []
    for item in payload[: config.POSTS_LIMIT]:
        if not isinstance(item, dict):
            logger.warning("Skipping malformed post payload: %r", item)
            continue

        try:
            posts.append(Post.from_api_payload(item))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping invalid post payload: %s", exc)

    logger.info("Fetched %d posts", len(posts))
    if not posts:
        logger.error("API returned no valid posts")
        return _fallback_posts("the API returned no valid posts")

    return posts
