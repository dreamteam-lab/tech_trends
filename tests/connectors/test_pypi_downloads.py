"""Tests for the PyPI BigQuery downloads connector."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from tech_trends.connectors import pypi_downloads


class FakeQueryJob:
    """Minimal BigQuery query job used by tests."""

    job_id = "test-job-id"
    total_bytes_processed = 12345

    def result(self) -> list[SimpleNamespace]:
        """Return fake daily download rows."""

        return [
            SimpleNamespace(
                download_date=date(2026, 8, 1),
                package_name="pandas",
                downloads=100,
            ),
            SimpleNamespace(
                download_date=date(2026, 8, 2),
                package_name="pandas",
                downloads=150,
            ),
        ]


def test_fetch_download_statistics_builds_query_and_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build parameterized SQL and aggregate returned BigQuery rows."""

    captured: dict[str, Any] = {}

    class FakeClient:
        """Capture arguments passed to the BigQuery client."""

        def __init__(self, *, project: str) -> None:
            captured["project"] = project

        def query(
            self,
            query: str,
            *,
            job_config: Any,
        ) -> FakeQueryJob:
            captured["query"] = query
            captured["job_config"] = job_config

            return FakeQueryJob()

    monkeypatch.setattr(
        pypi_downloads.bigquery,
        "Client",
        FakeClient,
    )

    date_from = datetime(2026, 8, 1, tzinfo=UTC)
    date_to = datetime(2026, 8, 3, tzinfo=UTC)

    data = pypi_downloads.fetch_download_statistics(
        package_name=" Pandas ",
        date_from=date_from,
        date_to=date_to,
        project_id="test-project",
    )

    assert captured["project"] == "test-project"
    assert captured["query"] == pypi_downloads.QUERY

    query_parameters = {
        parameter.name: parameter.value
        for parameter in captured["job_config"].query_parameters
    }

    assert query_parameters == {
        "date_from": date_from,
        "date_to": date_to,
        "package_name": "pandas",
    }

    assert data == {
        "package_name": "pandas",
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_downloads": 250,
        "daily_downloads": [
            {
                "download_date": "2026-08-01",
                "package_name": "pandas",
                "downloads": 100,
            },
            {
                "download_date": "2026-08-02",
                "package_name": "pandas",
                "downloads": 150,
            },
        ],
        "bigquery_job_id": "test-job-id",
        "total_bytes_processed": 12345,
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "package_name": " ",
            },
            "package_name must not be empty",
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
                "project_id": " ",
            },
            "project_id must not be empty",
        ),
    ],
)
def test_fetch_download_statistics_rejects_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    message: str,
) -> None:
    """Reject invalid arguments before creating a BigQuery client."""

    def fail_if_client_is_created(*args: object, **kwargs: object) -> None:
        pytest.fail("BigQuery client must not be created")

    monkeypatch.setattr(
        pypi_downloads.bigquery,
        "Client",
        fail_if_client_is_created,
    )

    arguments: dict[str, object] = {
        "package_name": "pandas",
        "date_from": datetime(2026, 8, 1, tzinfo=UTC),
        "date_to": datetime(2026, 8, 3, tzinfo=UTC),
        "project_id": "test-project",
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        pypi_downloads.fetch_download_statistics(**arguments)
