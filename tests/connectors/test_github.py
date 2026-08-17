"""Tests for the GitHub connector."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from tech_trends.connectors.github import fetch_repositories_page


BASE_URL = "https://api.github.com"


@respx.mock
def test_fetch_repositories_page_builds_search_request() -> None:
    """Send the expected search query, dates, page and token."""

    route = respx.get(
        f"{BASE_URL}/search/repositories",
        params={
            "q": (
                "python in:name,description "
                "created:2026-08-01..2026-08-02"
            ),
            "sort": "stars",
            "order": "desc",
            "per_page": 50,
            "page": 2,
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "total_count": 1,
                "incomplete_results": False,
                "items": [
                    {
                        "name": "example",
                        "stargazers_count": 10,
                    },
                ],
            },
            headers={
                "x-ratelimit-limit": "30",
                "x-ratelimit-remaining": "29",
                "x-ratelimit-used": "1",
                "x-ratelimit-reset": "1785720000",
                "x-ratelimit-resource": "search",
            },
        )
    )

    data, rate_limit = fetch_repositories_page(
        technology="python",
        date_from=datetime(2026, 8, 1, tzinfo=UTC),
        date_to=datetime(2026, 8, 3, tzinfo=UTC),
        page=2,
        token="test-token",
        page_size=50,
    )

    assert route.called
    assert data["items"][0]["name"] == "example"
    assert rate_limit["remaining"] == "29"
    assert rate_limit["resource"] == "search"

    request = route.calls.last.request

    assert request.headers["authorization"] == "Bearer test-token"
    assert request.headers["x-github-api-version"] == "2026-03-10"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "date_from": datetime(2026, 8, 3, tzinfo=UTC),
                "date_to": datetime(2026, 8, 1, tzinfo=UTC),
            },
            "date_from must be earlier than date_to",
        ),
        (
            {
                "page": 0,
            },
            "GitHub page must be greater than or equal to one",
        ),
        (
            {
                "page_size": 101,
            },
            "page_size must be between 1 and 100",
        ),
        (
            {
                "technology": " ",
            },
            "technology must not be empty",
        ),
        (
            {
                "token": " ",
            },
            "GitHub token must not be empty",
        ),
    ],
)
@respx.mock
def test_fetch_repositories_page_rejects_invalid_arguments(
    overrides: dict[str, object],
    message: str,
) -> None:
    """Reject invalid arguments before requesting GitHub."""

    arguments: dict[str, object] = {
        "technology": "python",
        "date_from": datetime(2026, 8, 1, tzinfo=UTC),
        "date_to": datetime(2026, 8, 3, tzinfo=UTC),
        "page": 1,
        "token": "test-token",
        "page_size": 100,
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        fetch_repositories_page(**arguments)

    assert not respx.calls.called
