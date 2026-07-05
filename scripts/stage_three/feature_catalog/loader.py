"""Load and normalize the Stage Three feature catalog contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import STAGE_THREE_FEATURE_CATALOG_PATH


DEFAULT_FEATURE_CATALOG_PATH = Path(STAGE_THREE_FEATURE_CATALOG_PATH)
DEFAULT_NORMALIZED_CATALOG_PATH = DEFAULT_FEATURE_CATALOG_PATH.with_name("feature_catalog.normalized.json")


def load_feature_catalog(path: str | Path = DEFAULT_FEATURE_CATALOG_PATH) -> dict[str, Any]:
    """Load a feature catalog from YAML or JSON-compatible YAML."""
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise FileNotFoundError(f"feature catalog does not exist: {catalog_path}")
    raw_text = catalog_path.read_text(encoding="utf-8")
    if not raw_text.strip():
        raise ValueError(f"feature catalog is empty: {catalog_path}")
    return _load_mapping(raw_text, catalog_path)


def save_normalized_catalog_snapshot(
    catalog: dict[str, Any],
    path: str | Path = DEFAULT_NORMALIZED_CATALOG_PATH,
) -> Path:
    """Write a deterministic JSON snapshot of the catalog and return its path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_feature_catalog(catalog)
    output_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def normalize_feature_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic catalog representation for tests and reports."""
    normalized: dict[str, Any] = {
        "version": str(catalog.get("version", "")),
        "project": str(catalog.get("project", "")),
        "stage": str(catalog.get("stage", "")),
        "owner": str(catalog.get("owner", "")),
        "source_document": str(catalog.get("source_document", "")),
        "forbidden_X_columns": sorted({str(item) for item in catalog.get("forbidden_X_columns", [])}),
        "feature_groups": {},
    }
    groups = catalog.get("feature_groups", {})
    if isinstance(groups, dict):
        for group_name in sorted(groups):
            raw_group = groups[group_name]
            if not isinstance(raw_group, dict):
                normalized["feature_groups"][group_name] = raw_group
                continue
            features = raw_group.get("features", [])
            normalized_group = {
                key: raw_group[key]
                for key in sorted(raw_group)
                if key != "features"
            }
            if isinstance(features, list):
                normalized_group["features"] = sorted(
                    features,
                    key=lambda feature: str(feature.get("name", "")) if isinstance(feature, dict) else str(feature),
                )
            else:
                normalized_group["features"] = features
            normalized["feature_groups"][group_name] = normalized_group
    return normalized


def _load_mapping(raw_text: str, path: Path) -> dict[str, Any]:
    loaded: Any
    try:
        import yaml  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        loaded = json.loads(raw_text)
    else:
        loaded = yaml.safe_load(raw_text)
    if not isinstance(loaded, dict):
        raise ValueError(f"feature catalog root must be a mapping: {path}")
    return loaded
