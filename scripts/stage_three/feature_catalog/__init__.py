"""Stage Three feature catalog loading and validation."""

from scripts.stage_three.feature_catalog.loader import (
    DEFAULT_NORMALIZED_CATALOG_PATH,
    load_feature_catalog,
    save_normalized_catalog_snapshot,
)
from scripts.stage_three.feature_catalog.validator import (
    FeatureCatalogValidationResult,
    validate_feature_catalog,
)

__all__ = [
    "DEFAULT_NORMALIZED_CATALOG_PATH",
    "FeatureCatalogValidationResult",
    "load_feature_catalog",
    "save_normalized_catalog_snapshot",
    "validate_feature_catalog",
]
