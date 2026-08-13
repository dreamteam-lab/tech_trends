"""Command-line interface for the Stack Overflow collector."""

import argparse
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from datetime import time as datetime_time
from pathlib import Path

import httpx

from tech_trends.connectors.stack_overflow import fetch_questions_page
from tech_trends.storage.raw import save_raw_response

MAX_PAGE_SIZE = 100


def positive_integer(value: str) -> int:
    """Convert a CLI argument to a positive integer."""

    number = int(value)

    if number <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return number


def page_size(value: str) -> int:
    """Validate Stack Overflow page size."""

    number = positive_integer(value)

    if number > MAX_PAGE_SIZE:
        raise argparse.ArgumentTypeError(
            f"Stack Overflow page size must not be greater than "
            f"{MAX_PAGE_SIZE}"
        )

    return number


def parse_arguments() -> argparse.Namespace:
    """Read and validate command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Collect Stack Overflow questions for a tag."
    )

    parser.add_argument(
        "--tag",
        required=True,
        help="Stack Overflow tag, for example python or reactjs.",
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
        help="Questions requested per page, from 1 to 100.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the Stack Overflow collector."""

    arguments = parse_arguments()

    tag = arguments.tag.strip()
    days = arguments.days
    questions_per_page = arguments.page_size

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    key = os.getenv("STACK_EXCHANGE_KEY", "").strip() or None

    if not tag:
        print(
            "Collection failed: tag must not be empty",
            file=sys.stderr,
        )
        return 1

    today_utc = datetime.now(UTC).date()
    date_to = datetime.combine(
        today_utc,
        datetime_time.min,
        tzinfo=UTC,
    )
    date_from = date_to - timedelta(days=days)

    print(
        f"Collecting Stack Overflow questions tagged {tag!r} "
        f"from {date_from.isoformat()} to {date_to.isoformat()}"
    )

    current_page = 1
    total_questions_collected = 0
    pages_collected = 0
    quota_remaining: int | None = None

    try:
        while True:
            page_data = fetch_questions_page(
                tag=tag,
                date_from=date_from,
                date_to=date_to,
                page=current_page,
                page_size=questions_per_page,
                key=key,
            )

            page_path = save_raw_response(
                data=page_data,
                data_dir=data_dir,
                source="stack_overflow",
                query=tag,
                page=current_page,
            )

            questions_on_page = len(page_data.get("items", []))
            total_questions_collected += questions_on_page
            pages_collected += 1

            quota_remaining = page_data.get("quota_remaining")

            print(
                f"Saved page {current_page} with "
                f"{questions_on_page} questions to {page_path}"
            )

            print(
                f"Stack Exchange quota remaining: {quota_remaining}"
            )

            if not page_data.get("has_more", False):
                break

            backoff = page_data.get("backoff", 0)

            if backoff:
                print(
                    f"Stack Exchange requested a {backoff}-second backoff"
                )
                time.sleep(backoff)

            current_page += 1

    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code

        if status_code == 400:
            message = "Stack Exchange rejected request parameters or API key"
        elif status_code in {429, 502}:
            message = "Stack Exchange rate limit was exceeded"
        elif status_code == 503:
            message = "Stack Exchange API is temporarily unavailable"
        else:
            message = f"Stack Exchange returned HTTP {status_code}"

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

    except ValueError as error:
        print(
            f"Collection failed on page {current_page}: {error}",
            file=sys.stderr,
        )
        return 1

    print(f"Collected {total_questions_collected} questions")
    print(f"Collected {pages_collected} pages")
    print(f"Final Stack Exchange quota remaining: {quota_remaining}")
    print("Stack Overflow collection completed successfully")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
