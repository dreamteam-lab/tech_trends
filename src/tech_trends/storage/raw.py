"""Persistence for unmodified API responses."""

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3


def save_raw_response(
    *,
    data: dict[str, Any],
    data_dir: Path,
    source: str,
    query: str,
    page: int,
) -> Path | str:
    """Save a complete API response to the configured raw data layer."""

    fetched_at = datetime.now(UTC)
    safe_query = _make_filename_safe(query)
    timestamp = fetched_at.strftime("%Y%m%dT%H%M%S%fZ")
    filename = f"{safe_query}_{timestamp}_page_{page}.json"

    storage_backend = os.getenv(
        "RAW_STORAGE_BACKEND",
        "local",
    ).strip().lower()

    if storage_backend == "local":
        return _save_to_local_storage(
            data=data,
            data_dir=data_dir,
            source=source,
            fetched_at=fetched_at,
            filename=filename,
        )

    if storage_backend == "s3":
        return _save_to_s3_storage(
            data=data,
            source=source,
            fetched_at=fetched_at,
            filename=filename,
        )

    raise ValueError(
        f"Unsupported RAW_STORAGE_BACKEND: {storage_backend}"
    )


def _save_to_local_storage(
    *,
    data: dict[str, Any],
    data_dir: Path,
    source: str,
    fetched_at: datetime,
    filename: str,
) -> Path:
    """Save a response as a local JSON file."""

    target_dir = (
        data_dir
        / "raw"
        / source
        / fetched_at.strftime("%Y")
        / fetched_at.strftime("%m")
        / fetched_at.strftime("%d")
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / filename
    temporary_path = target_path.with_suffix(".json.tmp")

    temporary_path.write_text(
        _serialize_response(data),
        encoding="utf-8",
    )
    temporary_path.replace(target_path)

    return target_path


def _save_to_s3_storage(
    *,
    data: dict[str, Any],
    source: str,
    fetched_at: datetime,
    filename: str,
) -> str:
    """Upload a response as a JSON object to the Bronze S3 bucket."""

    endpoint_url = os.getenv("S3_ENDPOINT_URL", "").strip()
    bucket = os.getenv(
        "S3_BRONZE_BUCKET",
        "tech-trends-bronze",
    ).strip()

    if not endpoint_url:
        raise ValueError(
            "S3_ENDPOINT_URL must be set when "
            "RAW_STORAGE_BACKEND=s3"
        )

    if not bucket:
        raise ValueError(
            "S3_BRONZE_BUCKET must not be empty"
        )

    object_key = "/".join(
        (
            source,
            fetched_at.strftime("%Y"),
            fetched_at.strftime("%m"),
            fetched_at.strftime("%d"),
            filename,
        )
    )

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
    )
    s3_client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=_serialize_response(data).encode("utf-8"),
        ContentType="application/json",
    )

    return f"s3://{bucket}/{object_key}"


def _serialize_response(
    data: dict[str, Any],
) -> str:
    """Serialize an API response as readable UTF-8 JSON."""

    return (
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def _make_filename_safe(value: str) -> str:
    """Convert a search query into a safe filename fragment."""

    normalized = value.strip().lower()
    safe_value = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        normalized,
    )

    return safe_value.strip("_") or "unknown"
