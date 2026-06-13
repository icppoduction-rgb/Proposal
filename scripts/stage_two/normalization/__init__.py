"""Normalization contracts and helpers for Stage Two."""

from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.schema_contracts import (
    NormalizedSchemaContract,
    NormalizedSchemaRegistry,
    register_default_normalized_schema,
)

__all__ = [
    "DnsNormalizationService",
    "NormalizedSchemaContract",
    "NormalizedSchemaRegistry",
    "register_default_normalized_schema",
]
