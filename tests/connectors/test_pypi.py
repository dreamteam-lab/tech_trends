"""Tests for the PyPI metadata connector."""

import httpx
import pytest
import respx

from tech_trends.connectors.pypi import fetch_project_metadata


BASE_URL = "https://pypi.org"


@respx.mock
def test_fetch_project_metadata_returns_data_and_headers() -> None:
    """Return PyPI project data and selected response headers."""

    route = respx.get(
        f"{BASE_URL}/pypi/pandas/json"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "info": {
                    "name": "pandas",
                    "version": "2.3.1",
                },
                "releases": {},
            },
            headers={
                "etag": '"test-etag"',
                "x-pypi-last-serial": "123456",
                "cache-control": "max-age=900",
            },
        )
    )

    data, metadata = fetch_project_metadata(
        package_name=" pandas ",
    )

    assert route.called
    assert data["info"]["name"] == "pandas"
    assert data["info"]["version"] == "2.3.1"

    assert metadata == {
        "etag": '"test-etag"',
        "last_serial": "123456",
        "cache_control": "max-age=900",
    }


@respx.mock
def test_fetch_project_metadata_rejects_empty_package() -> None:
    """Reject an empty package before making an HTTP request."""

    with pytest.raises(
        ValueError,
        match="package_name must not be empty",
    ):
        fetch_project_metadata(
            package_name="   ",
        )

    assert not respx.calls.called


@respx.mock
def test_fetch_project_metadata_raises_for_http_error() -> None:
    """Propagate an HTTP error returned by PyPI."""

    route = respx.get(
        f"{BASE_URL}/pypi/missing-package/json"
    ).mock(
        return_value=httpx.Response(
            404,
            json={
                "message": "Not Found",
            },
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as error_info:
        fetch_project_metadata(
            package_name="missing-package",
        )

    assert route.called
    assert error_info.value.response.status_code == 404
