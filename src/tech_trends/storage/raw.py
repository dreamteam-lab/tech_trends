"""Persistence for unmodified API responses."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def save_raw_response(
    *,
    data: dict[str, Any],
    data_dir: Path,
    source: str,
    query: str,
    page: int,
) -> Path:
    """Save a complete API response to the raw data layer."""
    fetched_at = datetime.now(UTC)
    safe_query = _make_filename_safe(query)

    target_dir = (
        data_dir
        / "raw"
        / source
        / fetched_at.strftime("%Y")
        / fetched_at.strftime("%m")
        / fetched_at.strftime("%d")
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = fetched_at.strftime("%Y%m%dT%H%M%S%fZ")
    target_path = target_dir / f"{safe_query}_{timestamp}_page_{page}.json"
    temporary_path = target_path.with_suffix(".json.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")

    temporary_path.replace(target_path)

    return target_path


def _make_filename_safe(value: str) -> str:
    """Convert a search query into a safe filename fragment."""
    normalized = value.strip().lower()
    safe_value = re.sub(r"[^a-z0-9_-]+", "_", normalized)

    return safe_value.strip("_") or "unknown"
