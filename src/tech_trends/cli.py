import argparse
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from tech_trends.connectors.hacker_news import fetch_stories_page
from tech_trends.storage.raw import save_raw_response


def positive_integer(value: str) -> int:
    """Convert a CLI argument to a positive integer."""
    number = int(value)

    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")

    return number


def parse_arguments() -> argparse.Namespace:
    """Read and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect Hacker News stories about a technology."
    )

    parser.add_argument(
        "--technology",
        required=True,
        help="Technology to search for, for example python, rust or postgresql.",
    )

    parser.add_argument(
        "--days",
        type=positive_integer,
        default=7,
        help="Number of previous days to collect. Default: 7.",
    )

    parser.add_argument(
        "--page-size",
        type=positive_integer,
        default=100,
        help="Number of stories requested per API page. Default: 100.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the Hacker News collector."""
    arguments = parse_arguments()

    technology = arguments.technology.strip()
    days = arguments.days
    page_size = arguments.page_size
    data_dir = Path(os.getenv("DATA_DIR", "data"))

    if not technology:
        print("Collection failed: technology must not be empty", file=sys.stderr)
        return 1

    date_to = datetime.now(UTC)
    date_from = date_to - timedelta(days=days)

    print(
        f"Collecting Hacker News stories about {technology!r} "
        f"from {date_from.isoformat()} to {date_to.isoformat()}"
    )

    current_page = 0
    total_stories_collected = 0

    try:
        first_page_data = fetch_stories_page(
            technology=technology,
            date_from=date_from,
            date_to=date_to,
            page=current_page,
            limit=page_size,
        )

        first_page_path = save_raw_response(
            data=first_page_data,
            data_dir=data_dir,
            source="hacker_news",
            query=technology,
            page=current_page,
        )

        total_pages = first_page_data["nbPages"]
        total_hits_reported = first_page_data["nbHits"]
        stories_on_first_page = len(first_page_data["hits"])
        total_stories_collected += stories_on_first_page

        print(
            f"Saved page {current_page} with {stories_on_first_page} stories "
            f"to {first_page_path}"
        )

        for page in range(1, total_pages):
            current_page = page

            page_data = fetch_stories_page(
                technology=technology,
                date_from=date_from,
                date_to=date_to,
                page=current_page,
                limit=page_size,
            )

            page_path = save_raw_response(
                data=page_data,
                data_dir=data_dir,
                source="hacker_news",
                query=technology,
                page=current_page,
            )

            stories_on_page = len(page_data["hits"])
            total_stories_collected += stories_on_page

            print(
                f"Saved page {current_page} with {stories_on_page} stories "
                f"to {page_path}"
            )

    except httpx.HTTPStatusError as error:
        print(
            f"Collection failed on page {current_page}: "
            f"Hacker News returned HTTP {error.response.status_code}",
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

    print(f"API reported {total_hits_reported} matching stories")
    print(f"Collected {total_stories_collected} stories")
    print(f"Collected {total_pages} pages")
    print("Collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
