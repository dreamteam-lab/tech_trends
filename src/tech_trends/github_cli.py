import argparse
import math
import os
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

import httpx

from tech_trends.connectors.github import fetch_repositories_page
from tech_trends.storage.raw import save_raw_response


GITHUB_SEARCH_MAX_RESULTS = 1000


def positive_integer(value: str) -> int:
    """Convert a CLI argument to a positive integer."""
    number = int(value)

    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")

    return number


def page_size(value: str) -> int:
    """Validate GitHub page size."""
    number = positive_integer(value)

    if number > 100:
        raise argparse.ArgumentTypeError(
            "GitHub page size must not be greater than 100"
        )

    return number


def parse_arguments() -> argparse.Namespace:
    """Read and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect GitHub repositories related to a technology."
    )

    parser.add_argument(
        "--technology",
        required=True,
        help="Technology to search for, for example python or clickhouse.",
    )

    parser.add_argument(
        "--days",
        type=positive_integer,
        default=7,
        help="Number of complete UTC days to collect. Default: 7.",
    )

    parser.add_argument(
        "--page-size",
        type=page_size,
        default=100,
        help="Repositories requested per page, from 1 to 100.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the GitHub repository collector."""
    arguments = parse_arguments()

    technology = arguments.technology.strip()
    days = arguments.days
    repositories_per_page = arguments.page_size
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    token = os.getenv("GITHUB_TOKEN", "").strip()

    if not technology:
        print("Collection failed: technology must not be empty", file=sys.stderr)
        return 1

    if not token:
        print(
            "Collection failed: GITHUB_TOKEN is not configured",
            file=sys.stderr,
        )
        return 1

    today_utc = datetime.now(UTC).date()
    date_to = datetime.combine(today_utc, time.min, tzinfo=UTC)
    date_from = date_to - timedelta(days=days)

    print(
        f"Collecting GitHub repositories about {technology!r} "
        f"from {date_from.isoformat()} to {date_to.isoformat()}"
    )

    current_page = 1
    total_repositories_collected = 0

    try:
        first_page_data, rate_limit = fetch_repositories_page(
            technology=technology,
            date_from=date_from,
            date_to=date_to,
            page=current_page,
            token=token,
            page_size=repositories_per_page,
        )

        first_page_path = save_raw_response(
            data=first_page_data,
            data_dir=data_dir,
            source="github",
            query=technology,
            page=current_page,
        )

        total_count = first_page_data["total_count"]
        incomplete_results = first_page_data["incomplete_results"]

        accessible_count = min(total_count, GITHUB_SEARCH_MAX_RESULTS)

        total_pages = max(
            1,
            math.ceil(accessible_count / repositories_per_page),
        )

        repositories_on_first_page = len(first_page_data["items"])
        total_repositories_collected += repositories_on_first_page

        print(
            f"Saved page {current_page} with "
            f"{repositories_on_first_page} repositories "
            f"to {first_page_path}"
        )

        print(
            "GitHub Search rate limit: "
            f"{rate_limit['remaining']}/{rate_limit['limit']} remaining; "
            f"resource={rate_limit['resource']}"
        )

        for page in range(2, total_pages + 1):
            current_page = page

            page_data, rate_limit = fetch_repositories_page(
                technology=technology,
                date_from=date_from,
                date_to=date_to,
                page=current_page,
                token=token,
                page_size=repositories_per_page,
            )

            page_path = save_raw_response(
                data=page_data,
                data_dir=data_dir,
                source="github",
                query=technology,
                page=current_page,
            )

            repositories_on_page = len(page_data["items"])
            total_repositories_collected += repositories_on_page

            print(
                f"Saved page {current_page} with "
                f"{repositories_on_page} repositories "
                f"to {page_path}"
            )

            print(
                "GitHub Search rate limit: "
                f"{rate_limit['remaining']}/{rate_limit['limit']} remaining"
            )

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        remaining = error.response.headers.get("x-ratelimit-remaining")
        reset = error.response.headers.get("x-ratelimit-reset")

        if status_code == 401:
            message = "GitHub rejected GITHUB_TOKEN"
        elif status_code in {403, 429}:
            message = (
                "GitHub rate limit or access restriction; "
                f"remaining={remaining}, reset={reset}"
            )
        else:
            message = f"GitHub returned HTTP {status_code}"

        print(
            f"Collection failed on page {current_page}: {message}",
            file=sys.stderr,
        )
        return 1

    except httpx.RequestError as error:
        print(
            f"Collection failed on page {current_page}: "
            f"network error while requesting {error.request.url}: {error}",
            file=sys.stderr,
        )
        return 1

    print(f"GitHub reported {total_count} matching repositories")
    print(
        f"Collected {total_repositories_collected} "
        f"of {accessible_count} accessible repositories"
    )
    print(f"Collected {total_pages} pages")

    if incomplete_results:
        print(
            "Warning: GitHub marked search results as incomplete",
            file=sys.stderr,
        )

    if total_count > GITHUB_SEARCH_MAX_RESULTS:
        print(
            "Warning: GitHub Search exposes only the first "
            f"{GITHUB_SEARCH_MAX_RESULTS} results for one query",
            file=sys.stderr,
        )

    print("GitHub collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
