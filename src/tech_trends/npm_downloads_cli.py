"""Command-line interface for the npm downloads collector."""

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from tech_trends.connectors.npm_downloads import fetch_download_statistics
from tech_trends.storage.raw import save_raw_response


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Collect daily download counts for one npm package."
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Exact npm package name, for example react or @nestjs/core.",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of complete UTC days to collect. Default: 7.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the npm downloads collector."""

    arguments = parse_arguments()

    package_name = arguments.package.strip()
    data_dir = Path(os.getenv("DATA_DIR", "data"))

    if not package_name:
        print(
            "Collection failed: package name must not be empty",
            file=sys.stderr,
        )
        return 1

    if arguments.days <= 0:
        print(
            "Collection failed: days must be greater than zero",
            file=sys.stderr,
        )
        return 1

    date_to = datetime.now(UTC).date() - timedelta(days=1)
    date_from = date_to - timedelta(days=arguments.days - 1)

    print(
        f"Collecting npm downloads for {package_name!r} "
        f"from {date_from.isoformat()} to {date_to.isoformat()}"
    )

    try:
        data = fetch_download_statistics(
            package_name=package_name,
            date_from=date_from,
            date_to=date_to,
        )

        output_path = save_raw_response(
            data=data,
            data_dir=data_dir,
            source="npm_downloads",
            query=package_name,
            page=0,
        )

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code

        if status_code == 404:
            message = f"npm package {package_name!r} was not found"
        elif status_code == 429:
            message = "npm rate limit was exceeded"
        else:
            message = f"npm Downloads API returned HTTP {status_code}"

        print(
            f"Collection failed: {message}",
            file=sys.stderr,
        )
        return 1

    except httpx.RequestError as error:
        print(
            "Collection failed: "
            f"network error while requesting {error.request.url}: {error}",
            file=sys.stderr,
        )
        return 1

    except ValueError as error:
        print(
            f"Collection failed: {error}",
            file=sys.stderr,
        )
        return 1

    daily_downloads = data.get("downloads", [])
    total_downloads = sum(
        item.get("downloads", 0)
        for item in daily_downloads
    )

    print(f"Collected {len(daily_downloads)} daily rows")
    print(f"Total downloads: {total_downloads}")
    print(f"Raw response saved to {output_path}")
    print("npm downloads collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
