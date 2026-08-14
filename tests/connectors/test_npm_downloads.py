"""Tests for the npm downloads connector."""

from datetime import date

import httpx
import pytest
import respx

from tech_trends.connectors.npm_downloads import fetch_download_statistics


BASE_URL = "https://api.npmjs.org"


@respx.mock
def test_fetch_download_statistics_returns_daily_downloads() -> None:
    """Return daily npm download statistics for an inclusive period."""

    route = respx.get(
        f"{BASE_URL}/downloads/range/"
        "2026-08-01:2026-08-02/react"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "start": "2026-08-01",
                "end": "2026-08-02",
                "package": "react",
                "downloads": [
                    {
                        "day": "2026-08-01",
                        "downloads": 100,
                    },
                    {
                        "day": "2026-08-02",
                        "downloads": 120,
                    },
                ],
            },
        )
    )

    data = fetch_download_statistics(
        package_name=" React ",
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 2),
    )

    assert route.called
    assert data["package"] == "react"
    assert len(data["downloads"]) == 2
    assert data["downloads"][1]["downloads"] == 120


@respx.mock
def test_fetch_download_statistics_encodes_scoped_package() -> None:
    """Encode a scoped npm package in the request URL."""

    route = respx.get(
        f"{BASE_URL}/downloads/range/"
        "2026-08-01:2026-08-01/%40nestjs%2Fcore"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "start": "2026-08-01",
                "end": "2026-08-01",
                "package": "@nestjs/core",
                "downloads": [],
            },
        )
    )

    data = fetch_download_statistics(
        package_name=" @NestJS/Core ",
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 1),
    )

    assert route.called
    assert data["package"] == "@nestjs/core"


@respx.mock
def test_fetch_download_statistics_rejects_empty_package() -> None:
    """Reject an empty package before making an HTTP request."""

    with pytest.raises(
        ValueError,
        match="package_name must not be empty",
    ):
        fetch_download_statistics(
            package_name=" ",
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 2),
        )

    assert not respx.calls.called


@respx.mock
def test_fetch_download_statistics_rejects_reversed_period() -> None:
    """Reject a period whose first date is later than its last date."""

    with pytest.raises(
        ValueError,
        match="date_from must not be later than date_to",
    ):
        fetch_download_statistics(
            package_name="react",
            date_from=date(2026, 8, 2),
            date_to=date(2026, 8, 1),
        )

    assert not respx.calls.called


@respx.mock
def test_fetch_download_statistics_raises_for_http_error() -> None:
    """Propagate an HTTP error returned by npm Downloads API."""

    route = respx.get(
        f"{BASE_URL}/downloads/range/"
        "2026-08-01:2026-08-01/missing-package"
    ).mock(
        return_value=httpx.Response(
            404,
            json={
                "error": "package not found",
            },
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as error_info:
        fetch_download_statistics(
            package_name="missing-package",
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 1),
        )

    assert route.called
    assert error_info.value.response.status_code == 404
