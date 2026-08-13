import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import DefaultCredentialsError

from tech_trends.connectors.pypi_downloads import fetch_download_statistics
from tech_trends.storage.raw import save_raw_response


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect daily download counts for one PyPI package."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Exact PyPI package name, for example pandas or apache-airflow.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of complete UTC days to collect. Default: 7.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the PyPI downloads collector."""
    arguments = parse_arguments()
    package_name = arguments.package.strip()
    project_id = os.getenv("GCP_PROJECT_ID", "").strip()
    data_dir = Path(os.getenv("DATA_DIR", "data"))

    if not package_name:
        print("Collection failed: package name must not be empty", file=sys.stderr)
        return 1

    if arguments.days <= 0:
        print("Collection failed: days must be greater than zero", file=sys.stderr)
        return 1

    if not project_id:
        print("Collection failed: GCP_PROJECT_ID is not configured", file=sys.stderr)
        return 1

    date_to = datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0)
    date_from = date_to - timedelta(days=arguments.days)

    print(
        f"Collecting PyPI downloads for {package_name!r} "
        f"from {date_from.isoformat()} to {date_to.isoformat()}"
    )

    try:
        data = fetch_download_statistics(
            package_name=package_name,
            date_from=date_from,
            date_to=date_to,
            project_id=project_id,
        )
        output_path = save_raw_response(
            data=data,
            data_dir=data_dir,
            source="pypi_downloads",
            query=package_name,
            page=0,
        )
    except DefaultCredentialsError:
        print(
            "Collection failed: Google Application Default Credentials "
            "were not found",
            file=sys.stderr,
        )
        return 1
    except GoogleAPIError as error:
        print(
            f"Collection failed: BigQuery returned an error: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Collection failed: {error}", file=sys.stderr)
        return 1

    print(f"Collected {len(data['daily_downloads'])} daily rows")
    print(f"Total downloads: {data['total_downloads']}")
    print(f"BigQuery bytes processed: {data['total_bytes_processed']}")
    print(f"Raw response saved to {output_path}")
    print("PyPI downloads collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
