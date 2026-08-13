"""Connector for Stack Overflow questions."""

from datetime import datetime
from typing import Any

import httpx

BASE_URL = "https://api.stackexchange.com"
API_VERSION = "2.3"
MAX_PAGE_SIZE = 100


def fetch_questions_page(
    *,
    tag: str,
    date_from: datetime,
    date_to: datetime,
    page: int,
    page_size: int = MAX_PAGE_SIZE,
    key: str | None = None,
) -> dict[str, Any]:
    """Fetch one page of Stack Overflow questions for a tag."""

    normalized_tag = tag.strip().lower()

    if not normalized_tag:
        raise ValueError("tag must not be empty")

    if date_from >= date_to:
        raise ValueError("date_from must be earlier than date_to")

    if page < 1:
        raise ValueError(
            "Stack Overflow page must be greater than or equal to one"
        )

    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be between 1 and {MAX_PAGE_SIZE}"
        )

    params: dict[str, str | int] = {
        "site": "stackoverflow",
        "tagged": normalized_tag,
        "fromdate": int(date_from.timestamp()),
        "todate": int(date_to.timestamp()) - 1,
        "sort": "creation",
        "order": "asc",
        "page": page,
        "pagesize": page_size,
    }

    if key and key.strip():
        params["key"] = key.strip()

    response = httpx.get(
        f"{BASE_URL}/{API_VERSION}/questions",
        params=params,
        headers={
            "Accept": "application/json",
            "User-Agent": "tech-trends-collector",
        },
        timeout=20.0,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    return data
