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
        return []
    except requests.RequestException as exc:
        logger.error("API request failed: %s", exc)
        return []
    except ValueError as exc:
        logger.error("API returned invalid JSON: %s", exc)
        return []

    if not isinstance(payload, list):
        logger.error("API returned unexpected payload type: %s", type(payload).__name__)
        return []

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
    return posts
