"""Central exclusions for Stage Two catalog inputs that must stay inactive."""

from __future__ import annotations

from pathlib import PurePath
from typing import Any


EXCLUDED_RAW_BUCKETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("host", "VALIDATION", "wls_day", ("host", "VALIDATION", "wls_day")),
)


def is_excluded_raw_bucket(
    *,
    branch: str,
    role: str,
    source_format: str,
    relative_path: str | PurePath | None,
) -> bool:
    """Return True for raw input buckets intentionally replaced by chunked files."""
    if relative_path is None:
        return False
    parts = _path_parts(relative_path)
    if not parts or parts[0].lower() == "chunked":
        return False
    for excluded_branch, excluded_role, excluded_format, excluded_prefix in EXCLUDED_RAW_BUCKETS:
        if (
            branch.lower() == excluded_branch
            and role.upper() == excluded_role
            and source_format == excluded_format
            and _matches_prefix(parts, excluded_prefix)
        ):
            return True
    return False


def is_excluded_dataset_file(file: Any) -> bool:
    """Return True when a DatasetFile-like object belongs to an excluded raw bucket."""
    return is_excluded_raw_bucket(
        branch=str(getattr(file, "branch", "")),
        role=str(getattr(file, "role", "")),
        source_format=str(getattr(file, "source_format", "")),
        relative_path=getattr(file, "relative_path", None),
    )


def _path_parts(path: str | PurePath) -> tuple[str, ...]:
    normalized = str(path).replace("\\", "/")
    return tuple(part for part in normalized.split("/") if part)


def _matches_prefix(parts: tuple[str, ...], prefix: tuple[str, ...]) -> bool:
    if len(parts) < len(prefix):
        return False
    return all(left.lower() == right.lower() for left, right in zip(parts, prefix))
