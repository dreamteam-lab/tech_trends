"""Tests for the npm metadata connector."""

import httpx
import pytest
import respx

from tech_trends.connectors.npm import fetch_package_metadata


BASE_URL = "https://registry.npmjs.org"


@respx.mock
def test_fetch_package_metadata_returns_data_and_headers() -> None:
    """Return package data and selected response headers."""

    route = respx.get(
        f"{BASE_URL}/react"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "react",
                "dist-tags": {
                    "latest": "19.2.8",
                },
                "versions": {},
            },
            headers={
                "etag": 'W/"test-etag"',
                "cache-control": "public, max-age=300",
                "last-modified": "Mon, 10 Aug 2026 00:00:00 GMT",
            },
        )
    )

    data, metadata = fetch_package_metadata(
        package_name=" React ",
    )

    assert route.called
    assert data["name"] == "react"
    assert data["dist-tags"]["latest"] == "19.2.8"

    assert metadata == {
        "etag": 'W/"test-etag"',
        "cache_control": "public, max-age=300",
        "last_modified": "Mon, 10 Aug 2026 00:00:00 GMT",
    }


@respx.mock
def test_fetch_package_metadata_rejects_empty_package_name() -> None:
    """Reject an empty package name without making an HTTP request."""

    with pytest.raises(
        ValueError,
        match="package_name must not be empty",
    ):
        fetch_package_metadata(
            package_name="   ",
        )

    assert not respx.calls.called


@respx.mock
def test_fetch_package_metadata_raises_for_http_error() -> None:
    """Propagate an HTTP error returned by npm Registry."""

    route = respx.get(
        f"{BASE_URL}/missing-package"
    ).mock(
        return_value=httpx.Response(
            404,
            json={
                "error": "Not found",
            },
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as error_info:
        fetch_package_metadata(
            package_name="missing-package",
        )

    assert route.called
    assert error_info.value.response.status_code == 404


@respx.mock
def test_fetch_package_metadata_encodes_scoped_package_name() -> None:
    """Encode the slash and special characters in a scoped package name."""

    route = respx.get(
        f"{BASE_URL}/%40nestjs%2Fcore"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "@nestjs/core",
                "dist-tags": {
                    "latest": "11.0.0",
                },
                "versions": {},
            },
        )
    )

    data, _ = fetch_package_metadata(
        package_name=" @NestJS/Core ",
    )

    assert route.called
    assert data["name"] == "@nestjs/core"
