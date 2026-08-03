from datetime import datetime
from typing import Any
import httpx

BASE_URL = "https://hn.algolia.com/api/v1"


def fetch_stories_page(
    technology: str,
    date_from: datetime,
    date_to: datetime,
    page: int,
    limit: int = 100,
) -> dict[str, Any]:

    if date_from >= date_to:
        raise ValueError("date_from must be earlier than date_to")

    if page < 0:
        raise ValueError("page must be greater than or equal to zero")

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    date_from_timestamp = int(date_from.timestamp())
    date_to_timestamp = int(date_to.timestamp())

    response = httpx.get(
        f"{BASE_URL}/search_by_date",
        params={
            "query": technology,
            "tags": "story",
            "numericFilters": (
                f"created_at_i>={date_from_timestamp},"
                f"created_at_i<{date_to_timestamp}"
            ),
            "hitsPerPage": limit,
            "page": page,
        },
        timeout=20.0,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    return data
