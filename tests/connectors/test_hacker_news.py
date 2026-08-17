"""Tests for the Hacker News connector."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from tech_trends.connectors.hacker_news import fetch_stories_page


BASE_URL = "https://hn.algolia.com/api/v1"


@respx.mock
def test_fetch_stories_page_builds_search_request() -> None:
    """Send the expected technology, timestamps and page settings."""

    date_from = datetime(2026, 8, 1, tzinfo=UTC)
    date_to = datetime(2026, 8, 3, tzinfo=UTC)

    route = respx.get(
        f"{BASE_URL}/search_by_date",
        params={
            "query": "python",
            "tags": "story",
            "numericFilters": (
                f"created_at_i>={int(date_from.timestamp())},"
                f"created_at_i<{int(date_to.timestamp())}"
            ),
            "hitsPerPage": 50,
            "page": 0,
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": [
                    {
                        "objectID": "123",
                        "title": "Python release",
                        "points": 42,
                    },
                ],
                "nbHits": 1,
                "page": 0,
                "nbPages": 1,
            },
        )
    )

    data = fetch_stories_page(
        technology="python",
        date_from=date_from,
        date_to=date_to,
        page=0,
        limit=50,
    )

    assert route.called
    assert data["nbHits"] == 1
    assert data["hits"][0]["objectID"] == "123"


@pytest.mark.parametrize(
    ("date_from", "date_to", "page", "limit", "message"),
    [
        (
            datetime(2026, 8, 3, tzinfo=UTC),
            datetime(2026, 8, 1, tzinfo=UTC),
            0,
            100,
            "date_from must be earlier than date_to",
        ),
        (
            datetime(2026, 8, 1, tzinfo=UTC),
            datetime(2026, 8, 3, tzinfo=UTC),
            -1,
            100,
            "page must be greater than or equal to zero",
        ),
        (
            datetime(2026, 8, 1, tzinfo=UTC),
            datetime(2026, 8, 3, tzinfo=UTC),
            0,
            0,
            "limit must be greater than zero",
        ),
    ],
)
@respx.mock
def test_fetch_stories_page_rejects_invalid_arguments(
    date_from: datetime,
    date_to: datetime,
    page: int,
    limit: int,
    message: str,
) -> None:
    """Reject invalid period and pagination arguments."""

    with pytest.raises(ValueError, match=message):
        fetch_stories_page(
            technology="python",
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )

    assert not respx.calls.called


@respx.mock
def test_fetch_stories_page_raises_for_http_error() -> None:
    """Propagate an HTTP error returned by Hacker News API."""

    route = respx.get(
        f"{BASE_URL}/search_by_date"
    ).mock(
        return_value=httpx.Response(
            503,
            json={
                "message": "Unavailable",
            },
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as error_info:
        fetch_stories_page(
            technology="python",
            date_from=datetime(2026, 8, 1, tzinfo=UTC),
            date_to=datetime(2026, 8, 3, tzinfo=UTC),
            page=0,
        )

    assert route.called
    assert error_info.value.response.status_code == 503
