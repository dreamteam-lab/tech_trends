from datetime import datetime, timedelta
from typing import Any

import httpx


BASE_URL = "https://api.github.com"
API_VERSION = "2026-03-10"
MAX_PAGE_SIZE = 100


def fetch_repositories_page(
    *,
    technology: str,
    date_from: datetime,
    date_to: datetime,
    page: int,
    token: str,
    page_size: int = MAX_PAGE_SIZE,
) -> tuple[dict[str, Any], dict[str, str | None]]:
    """Fetch one page of GitHub repositories created in a period."""

    if date_from >= date_to:
        raise ValueError("date_from must be earlier than date_to")

    if page < 1:
        raise ValueError("GitHub page must be greater than or equal to one")

    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be between 1 and {MAX_PAGE_SIZE}"
        )

    if not technology.strip():
        raise ValueError("technology must not be empty")

    if not token.strip():
        raise ValueError("GitHub token must not be empty")

    first_date = date_from.date().isoformat()
    last_date = (date_to - timedelta(microseconds=1)).date().isoformat()

    search_query = (
        f"{technology.strip()} "
        f"in:name,description "
        f"created:{first_date}..{last_date}"
    )

    response = httpx.get(
        f"{BASE_URL}/search/repositories",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "tech-trends-collector",
        },
        params={
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": page_size,
            "page": page,
        },
        timeout=20.0,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    rate_limit = {
        "limit": response.headers.get("x-ratelimit-limit"),
        "remaining": response.headers.get("x-ratelimit-remaining"),
        "used": response.headers.get("x-ratelimit-used"),
        "reset": response.headers.get("x-ratelimit-reset"),
        "resource": response.headers.get("x-ratelimit-resource"),
    }

    return data, rate_limit
