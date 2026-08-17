"""Command-line interface for the npm metadata collector."""

import argparse
import os
import sys
from pathlib import Path

import httpx

from tech_trends.connectors.npm import fetch_package_metadata
from tech_trends.storage.raw import save_raw_response


def parse_arguments() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect metadata for one public npm package."
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Exact npm package name, for example react or @nestjs/core.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the npm metadata collector."""
    arguments = parse_arguments()

    package_name = arguments.package.strip()
    data_dir = Path(os.getenv("DATA_DIR", "data"))

    if not package_name:
        print(
            "Collection failed: package name must not be empty",
            file=sys.stderr,
        )
        return 1

    print(f"Collecting npm metadata for package {package_name!r}")

    try:
        package_data, response_metadata = fetch_package_metadata(
            package_name=package_name,
        )

        output_path = save_raw_response(
            data=package_data,
            data_dir=data_dir,
            source="npm",
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
            message = f"npm Registry returned HTTP {status_code}"

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

    latest_version = package_data.get("dist-tags", {}).get("latest")
    latest_data = package_data.get("versions", {}).get(
        latest_version,
        {},
    )

    print(f"Package name: {package_data.get('name')}")
    print(f"Latest version: {latest_version}")
    print(f"Description: {latest_data.get('description')}")
    print(f"License: {latest_data.get('license')}")
    print(
        "Number of versions: "
        f"{len(package_data.get('versions', {}))}"
    )
    print(f"ETag: {response_metadata['etag']}")
    print(f"Raw response saved to {output_path}")
    print("npm metadata collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
