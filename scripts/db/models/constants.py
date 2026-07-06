"""Shared catalog constraint values for Stage Two ORM models."""

BRANCH_VALUES: tuple[str, ...] = ("dns", "host", "network", "hybrid")
ROLE_VALUES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST", "EXPERIMENTS")
ACTIVE_DATASET_ROLE_VALUES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST")
ACTIVE_CATALOG_SOURCE_GROUP: str = "PATH_FOLDER_DATASETS_FILTER"
FILE_STATUS_VALUES: tuple[str, ...] = (
    "DISCOVERED",
    "REGISTERED",
    "CHANGED",
    "EMPTY_FILE",
    "UNSUPPORTED_FORMAT",
    "READY_FOR_PARSING",
    "PARSED",
    "PARTIALLY_PARSED",
    "FAILED",
    "SKIPPED",
)
RUN_STATUS_VALUES: tuple[str, ...] = (
    "PENDING",
    "RUNNING",
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILED",
    "SKIPPED",
    "BLOCKED",
    "BLOCKED_BY_LEAKAGE",
    "BLOCKED_BY_QUALITY",
)
PARSER_RUN_STATUS_VALUES: tuple[str, ...] = (
    "RUNNING",
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILED",
    "SKIPPED",
)
SCHEMA_LAYER_VALUES: tuple[str, ...] = ("normalized", "features", "model_ready")
LABEL_STATUS_VALUES: tuple[str, ...] = (
    "explicit_label",
    "inferred_label",
    "weak_label",
    "partial_label",
    "unlabeled",
    "conflicting_label",
)
MODEL_READY_DATA_TYPE_VALUES: tuple[str, ...] = (
    "X",
    "y",
    "metadata",
    "traceability",
    "sequence",
    "split_index",
    "preprocessing_metadata",
)
QUALITY_ARTIFACT_TYPE_VALUES: tuple[str, ...] = (
    "raw_file",
    "normalized",
    "feature",
    "model_ready",
    "preprocessing",
    "catalog",
)
QUALITY_STATUS_VALUES: tuple[str, ...] = (
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILED",
    "SKIPPED",
    "BLOCKED",
)
QUALITY_SEVERITY_VALUES: tuple[str, ...] = ("INFO", "WARNING", "ERROR", "CRITICAL")


def sql_in(values: tuple[str, ...]) -> str:
    """Format string values for SQL CHECK IN expressions."""
    return ", ".join(f"'{value}'" for value in values)
