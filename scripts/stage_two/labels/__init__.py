"""Label resolution utilities for Stage Two normalization."""

from scripts.stage_two.labels.resolver import (
    LabelResolution,
    LabelResolver,
    LabelResolverProtocol,
    LabelRule,
    UnlabeledLabelResolver,
    load_config_rules,
    resolve_embedded,
    resolve_filename,
    resolve_ids_alert,
    resolve_rules,
    unlabeled,
)

__all__ = [
    "LabelResolution",
    "LabelResolver",
    "LabelResolverProtocol",
    "LabelRule",
    "UnlabeledLabelResolver",
    "load_config_rules",
    "resolve_embedded",
    "resolve_filename",
    "resolve_ids_alert",
    "resolve_rules",
    "unlabeled",
]
