"""BigQuery connector for PyPI download statistics."""

from datetime import datetime
from typing import Any

from google.cloud import bigquery


QUERY = """
SELECT
    DATE(timestamp) AS download_date,
    file.project AS package_name,
    COUNT(*) AS downloads
FROM `bigquery-public-data.pypi.file_downloads`
WHERE timestamp >= @date_from
  AND timestamp < @date_to
  AND file.project = @package_name
GROUP BY download_date, package_name
ORDER BY download_date
"""


def fetch_download_statistics(
    *,
    package_name: str,
    date_from: datetime,
    date_to: datetime,
    project_id: str,
) -> dict[str, Any]:
    """Return daily download counts for one PyPI package."""
    normalized_package_name = package_name.strip().lower()

    if not normalized_package_name:
        raise ValueError("package_name must not be empty")

    if date_from >= date_to:
        raise ValueError("date_from must be earlier than date_to")

    if not project_id.strip():
        raise ValueError("project_id must not be empty")

    client = bigquery.Client(project=project_id)
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "date_from",
                "TIMESTAMP",
                date_from,
            ),
            bigquery.ScalarQueryParameter(
                "date_to",
                "TIMESTAMP",
                date_to,
            ),
            bigquery.ScalarQueryParameter(
                "package_name",
                "STRING",
                normalized_package_name,
            ),
        ]
    )

    query_job = client.query(QUERY, job_config=job_config)
    rows = query_job.result()

    daily_downloads = [
        {
            "download_date": row.download_date.isoformat(),
            "package_name": row.package_name,
            "downloads": row.downloads,
        }
        for row in rows
    ]

    return {
        "package_name": normalized_package_name,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_downloads": sum(row["downloads"] for row in daily_downloads),
        "daily_downloads": daily_downloads,
        "bigquery_job_id": query_job.job_id,
        "total_bytes_processed": query_job.total_bytes_processed,
    }
