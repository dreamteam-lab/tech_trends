from typing import Any
from urllib.parse import quote

import httpx


BASE_URL = "https://pypi.org"


def fetch_project_metadata(
    *,
    package_name: str,
) -> tuple[dict[str, Any], dict[str, str | None]]:

    normalized_package_name = package_name.strip()

    if not normalized_package_name:
        raise ValueError("package_name must not be empty")

    encoded_package_name = quote(
        normalized_package_name,
        safe="",
    )

    response = httpx.get(
        f"{BASE_URL}/pypi/{encoded_package_name}/json",
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
        "last_serial": response.headers.get("x-pypi-last-serial"),
        "cache_control": response.headers.get("cache-control"),
    }

    return data, response_metadata
