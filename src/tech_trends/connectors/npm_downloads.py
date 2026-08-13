"""Connector for npm download statistics."""

from datetime import date
from typing import Any
from urllib.parse import quote

import httpx

BASE_URL = "https://api.npmjs.org"


def fetch_download_statistics(
    *,
    package_name: str,
    date_from: date,
    date_to: date,
) -> dict[str, Any]:
    """Return daily download counts for one npm package."""

    normalized_package_name = package_name.strip().lower()

    if not normalized_package_name:
        raise ValueError("package_name must not be empty")

    if date_from > date_to:
        raise ValueError("date_from must not be later than date_to")

    encoded_package_name = quote(
        normalized_package_name,
        safe="",
    )

    period = (
        f"{date_from.isoformat()}:"
        f"{date_to.isoformat()}"
    )

    response = httpx.get(
        f"{BASE_URL}/downloads/range/"
        f"{period}/{encoded_package_name}",
        headers={
            "Accept": "application/json",
            "User-Agent": "tech-trends-collector",
        },
        timeout=20.0,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    return data
