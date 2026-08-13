import argparse
import os
import sys
from pathlib import Path

import httpx

from tech_trends.connectors.pypi import fetch_project_metadata
from tech_trends.storage.raw import save_raw_response


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect metadata for one PyPI package."
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Exact PyPI package name, for example pandas or apache-airflow.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the PyPI metadata collector."""
    arguments = parse_arguments()

    package_name = arguments.package.strip()
    data_dir = Path(os.getenv("DATA_DIR", "data"))

    if not package_name:
        print(
            "Collection failed: package name must not be empty",
            file=sys.stderr,
        )
        return 1

    print(f"Collecting PyPI metadata for package {package_name!r}")

    try:
        project_data, response_metadata = fetch_project_metadata(
            package_name=package_name,
        )

        output_path = save_raw_response(
            data=project_data,
            data_dir=data_dir,
            source="pypi",
            query=package_name,
            page=0,
        )

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code

        if status_code == 404:
            message = f"PyPI package {package_name!r} was not found"
        elif status_code == 429:
            message = "PyPI rate limit was exceeded"
        else:
            message = f"PyPI returned HTTP {status_code}"

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

    package_info = project_data["info"]
    releases = project_data.get("releases", {})

    print(f"Package name: {package_info.get('name')}")
    print(f"Latest version: {package_info.get('version')}")
    print(f"Summary: {package_info.get('summary')}")
    print(f"Python requirement: {package_info.get('requires_python')}")
    print(f"Number of releases: {len(releases)}")
    print(f"PyPI last serial: {response_metadata['last_serial']}")
    print(f"Raw response saved to {output_path}")
    print("PyPI metadata collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
