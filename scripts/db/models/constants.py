"""Shared catalog constraint values for Stage Two ORM models."""

BRANCH_VALUES: tuple[str, ...] = ("dns", "host", "network", "hybrid")
ROLE_VALUES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST", "EXPERIMENTS")
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
)
PARSER_RUN_STATUS_VALUES: tuple[str, ...] = (
    "RUNNING",
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "FAILED",
    "SKIPPED",
)
SCHEMA_LAYER_VALUES: tuple[str, ...] = ("normalized", "features", "model_ready")


def sql_in(values: tuple[str, ...]) -> str:
    """Format string values for SQL CHECK IN expressions."""
    return ", ".join(f"'{value}'" for value in values)
