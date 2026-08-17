"""Tests for the Stack Overflow connector."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from tech_trends.connectors.stack_overflow import fetch_questions_page


BASE_URL = "https://api.stackexchange.com"


@respx.mock
def test_fetch_questions_page_builds_tagged_request() -> None:
    """Send the expected tag, inclusive timestamps, page and key."""

    date_from = datetime(2026, 8, 1, tzinfo=UTC)
    date_to = datetime(2026, 8, 3, tzinfo=UTC)

    route = respx.get(
        f"{BASE_URL}/2.3/questions",
        params={
            "site": "stackoverflow",
            "tagged": "python",
            "fromdate": int(date_from.timestamp()),
            "todate": int(date_to.timestamp()) - 1,
            "sort": "creation",
            "order": "asc",
            "page": 2,
            "pagesize": 50,
            "key": "test-key",
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "question_id": 123,
                        "tags": [
                            "python",
                        ],
                        "score": 5,
                        "view_count": 100,
                        "answer_count": 2,
                    },
                ],
                "has_more": True,
                "backoff": 2,
                "quota_remaining": 9999,
            },
        )
    )

    data = fetch_questions_page(
        tag=" Python ",
        date_from=date_from,
        date_to=date_to,
        page=2,
        page_size=50,
        key=" test-key ",
    )

    assert route.called
    assert data["items"][0]["question_id"] == 123
    assert data["has_more"] is True
    assert data["backoff"] == 2
    assert data["quota_remaining"] == 9999


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "tag": " ",
            },
            "tag must not be empty",
        ),
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
            "Stack Overflow page must be greater than or equal to one",
        ),
        (
            {
                "page_size": 0,
            },
            "page_size must be between 1 and 100",
        ),
        (
            {
                "page_size": 101,
            },
            "page_size must be between 1 and 100",
        ),
    ],
)
@respx.mock
def test_fetch_questions_page_rejects_invalid_arguments(
    overrides: dict[str, object],
    message: str,
) -> None:
    """Reject invalid arguments before requesting Stack Exchange."""

    arguments: dict[str, object] = {
        "tag": "python",
        "date_from": datetime(2026, 8, 1, tzinfo=UTC),
        "date_to": datetime(2026, 8, 3, tzinfo=UTC),
        "page": 1,
        "page_size": 100,
        "key": None,
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        fetch_questions_page(**arguments)

    assert not respx.calls.called


@respx.mock
def test_fetch_questions_page_omits_empty_key() -> None:
    """Do not send an empty optional Stack Exchange key."""

    date_from = datetime(2026, 8, 1, tzinfo=UTC)
    date_to = datetime(2026, 8, 2, tzinfo=UTC)

    route = respx.get(
        f"{BASE_URL}/2.3/questions"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [],
                "has_more": False,
                "quota_remaining": 299,
            },
        )
    )

    fetch_questions_page(
        tag="python",
        date_from=date_from,
        date_to=date_to,
        page=1,
        key=" ",
    )

    assert route.called
    assert "key" not in route.calls.last.request.url.params
