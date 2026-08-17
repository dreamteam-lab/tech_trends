"""Connector for npm package metadata."""

from typing import Any
from urllib.parse import quote

import httpx

BASE_URL = "https://registry.npmjs.org"


def fetch_package_metadata(
    *,
    package_name: str,
) -> tuple[dict[str, Any], dict[str, str | None]]:
    """Fetch complete metadata for one public npm package."""

    normalized_package_name = package_name.strip().lower()

    if not normalized_package_name:
        raise ValueError("package_name must not be empty")

    encoded_package_name = quote(
        normalized_package_name,
        safe="",
    )

    response = httpx.get(
        f"{BASE_URL}/{encoded_package_name}",
        headers={
            "Accept": "application/json",
            "User-Agent": "tech-trends-collector",
        },
        timeout=20.0,
    )

    response.raise_for_status()

    data: dict[str, Any] = response.json()

    response_metadata = {
        "etag": response.headers.get("etag"),
        "cache_control": response.headers.get("cache-control"),
        "last_modified": response.headers.get("last-modified"),
    }

    return data, response_metadata
