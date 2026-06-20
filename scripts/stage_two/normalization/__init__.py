"""Normalization contracts and helpers for Stage Two."""

from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.normalization.runner import (
    NormalizeAllGroupResult,
    NormalizeAllRequest,
    NormalizeAllResult,
    NormalizeAllRunner,
    NormalizeFileResult,
    NormalizeFormatRequest,
    NormalizeFormatResult,
    NormalizeFormatRunner,
)
from scripts.stage_two.normalization.options import NormalizationOptions
from scripts.stage_two.normalization.schema_contracts import (
    NormalizedSchemaContract,
    NormalizedSchemaRegistry,
    register_default_normalized_schema,
)

__all__ = [
    "DnsNormalizationService",
    "HostNormalizationService",
    "NormalizeAllGroupResult",
    "NormalizeAllRequest",
    "NormalizeAllResult",
    "NormalizeAllRunner",
    "NormalizeFileResult",
    "NormalizeFormatRequest",
    "NormalizeFormatResult",
    "NormalizeFormatRunner",
    "NormalizationOptions",
    "NormalizedSchemaContract",
    "NormalizedSchemaRegistry",
    "register_default_normalized_schema",
]
