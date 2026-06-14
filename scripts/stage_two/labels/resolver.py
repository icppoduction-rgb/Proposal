"""Canonical label resolution for Stage Two normalized events."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from sqlalchemy.orm import Session

from config import LABEL_MAPPING_RULES_CONFIG
from scripts.db.models import LabelMappingRule
from scripts.db.repositories import LabelRepository

if TYPE_CHECKING:
    from scripts.stage_two.parsers.base import ParserContext


SOURCE_PRIORITY: dict[str, int] = {
    "embedded_column": 0,
    "ground_truth_csv": 1,
    "external_label_file": 1,
    "scenario_metadata": 2,
    "filename": 3,
    "ids_alert": 4,
    "none": 99,
}
EMBEDDED_LABEL_FIELDS: tuple[str, ...] = (
    "label_binary",
    "label",
    "labels",
    "target",
    "class",
    "is_attack",
    "is_malicious",
    "malicious",
    "attack",
    "attack_cat",
    "attack_category",
    "attack_subcat",
    "is_executing_exploit",
    "exploit",
)
BENIGN_TOKENS: frozenset[str] = frozenset({"0", "false", "benign", "normal", "clean", "legitimate"})
MALICIOUS_TOKEN_FAMILIES: dict[str, str] = {
    "1": "unknown",
    "true": "unknown",
    "attack": "unknown",
    "attacking": "unknown",
    "malicious": "unknown",
    "exploit": "unknown",
    "alert": "unknown",
    "malware": "malware",
    "phishing": "phishing",
    "spam": "spam",
    "exfil": "dns_exfiltration",
    "exfiltration": "dns_exfiltration",
    "tunnel": "dns_exfiltration",
    "tunneling": "dns_exfiltration",
    "dga": "dns_exfiltration",
    "crack_passwords": "privilege_escalation",
    "escalate": "privilege_escalation",
    "privilege": "privilege_escalation",
    "lateral": "lateral_movement",
    "nmap": "lateral_movement",
    "hping": "lateral_movement",
    "masscan": "lateral_movement",
    "zmap": "lateral_movement",
}
UNKNOWN_TOKENS: frozenset[str] = frozenset({"", "none", "null", "unknown", "unlabeled", "na", "n/a"})
DEFAULT_CONFIG_PATH = Path(LABEL_MAPPING_RULES_CONFIG) if LABEL_MAPPING_RULES_CONFIG else None


class LabelResolverProtocol(Protocol):
    """Protocol implemented by canonical and test label resolvers."""

    def resolve(self, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
        """Return canonical label fields for one normalized source row."""


@dataclass(frozen=True)
class LabelResolution:
    """Canonical label assignment with source and confidence metadata."""

    label_binary: int | None
    label_family: str | None
    label_subtype: str | None
    label_source: str
    label_status: str
    label_confidence: float | None
    label_mapping_rule_id: str | None = None

    def as_event_fields(self) -> dict[str, Any]:
        """Return normalized event label fields."""
        return {
            "label_binary": self.label_binary,
            "label_family": self.label_family,
            "label_subtype": self.label_subtype,
            "label_source": self.label_source,
            "label_status": self.label_status,
            "label_confidence": self.label_confidence,
            "label_mapping_rule_id": self.label_mapping_rule_id,
        }


@dataclass(frozen=True)
class LabelRule:
    """Runtime representation of one label mapping rule from DB or config."""

    rule_uid: str
    branch: str
    role: str | None
    source_format: str | None
    dataset_name_pattern: str | None
    file_name_pattern: str | None
    source_field: str | None
    source_value_pattern: str | None
    label_binary: int | None
    label_family: str | None
    label_subtype: str | None
    label_source: str
    label_status: str
    label_confidence: float | None
    priority: int


class UnlabeledLabelResolver:
    """Resolver that always returns explicit unlabeled fields."""

    def resolve(self, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
        """Return a canonical unlabeled result."""
        return unlabeled().as_event_fields()


class LabelResolver:
    """Resolve labels from embedded fields, DB/config rules, filenames, and weak alerts."""

    def __init__(
        self,
        *,
        session: Session | None = None,
        config_path: str | Path | None = None,
        config_rules: list[dict[str, Any]] | None = None,
        enable_filename_heuristics: bool = True,
    ) -> None:
        """Initialize the resolver with optional DB and config rule sources."""
        self.session = session
        self.config_path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
        self.config_rules = [rule_from_mapping(row) for row in (config_rules or [])]
        self.enable_filename_heuristics = enable_filename_heuristics

    def resolve(self, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
        """Return canonical label fields for one source row."""
        candidates = self._collect_candidates(row, context)
        if not candidates:
            return unlabeled().as_event_fields()
        selected = select_resolution(candidates)
        return selected.as_event_fields()

    def _collect_candidates(self, row: dict[str, Any], context: ParserContext) -> list[LabelResolution]:
        candidates: list[LabelResolution] = []
        candidates.extend(resolve_embedded(row))
        candidates.extend(resolve_rules(row, context, self._load_rules(context)))
        if self.enable_filename_heuristics:
            candidates.extend(resolve_filename(context))
        candidates.extend(resolve_ids_alert(row))
        return candidates

    def _load_rules(self, context: ParserContext) -> list[LabelRule]:
        rules = list(self.config_rules)
        rules.extend(load_config_rules(self.config_path))
        if self.session is not None:
            repository = LabelRepository(self.session)
            db_rules = repository.find_matching_rules(
                branch=context.branch,
                role=context.dataset_role,
                source_format=context.source_format,
            )
            rules.extend(rule_from_orm(rule) for rule in db_rules)
        return [
            rule
            for rule in rules
            if rule.branch == context.branch
            and (rule.role is None or rule.role == context.dataset_role)
            and (rule.source_format is None or rule.source_format == context.source_format)
        ]


def resolve_embedded(row: dict[str, Any]) -> list[LabelResolution]:
    """Resolve labels from direct label-like source fields."""
    candidates: list[LabelResolution] = []
    for field in EMBEDDED_LABEL_FIELDS:
        value = nested_get(row, field)
        if value in ("", None):
            continue
        candidate = resolution_from_value(
            value,
            source="embedded_column",
            status="explicit_label",
            confidence=1.0,
            subtype=str(value) if field in {"attack_subcat", "attack_category"} else None,
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def resolve_rules(row: dict[str, Any], context: ParserContext, rules: list[LabelRule]) -> list[LabelResolution]:
    """Resolve labels from matching DB/config mapping rules."""
    candidates: list[LabelResolution] = []
    for rule in sorted(rules, key=lambda item: (SOURCE_PRIORITY.get(item.label_source, 50), item.priority)):
        if not rule_matches(rule, row, context):
            continue
        candidates.append(
            LabelResolution(
                label_binary=rule.label_binary,
                label_family=rule.label_family,
                label_subtype=rule.label_subtype,
                label_source=rule.label_source,
                label_status=rule.label_status,
                label_confidence=rule.label_confidence,
                label_mapping_rule_id=rule.rule_uid,
            )
        )
    return candidates


def resolve_filename(context: ParserContext) -> list[LabelResolution]:
    """Resolve conservative filename labels for non-TEST datasets."""
    if context.dataset_role == "TEST":
        return []
    text = Path(context.source_file_path).as_posix().lower()
    tokens = tokenize_label_text(text)
    for token in tokens:
        if token in BENIGN_TOKENS:
            return [
                LabelResolution(0, "benign", None, "filename", "inferred_label", 0.8, "filename:benign")
            ]
    for token in tokens:
        family = MALICIOUS_TOKEN_FAMILIES.get(token)
        if family is not None:
            return [
                LabelResolution(
                    1,
                    None if family == "unknown" else family,
                    token,
                    "filename",
                    "inferred_label",
                    0.75,
                    f"filename:{token}",
                )
            ]
    return []


def resolve_ids_alert(row: dict[str, Any]) -> list[LabelResolution]:
    """Resolve weak labels from IDS alert-like fields."""
    alert_value = first_present(row, ("alert", "ids_alert", "rule.alert", "event_type", "event.action"))
    if alert_value in ("", None):
        return []
    text = str(alert_value).lower()
    if "alert" not in text and text not in {"true", "1"}:
        return []
    return [LabelResolution(1, None, None, "ids_alert", "weak_label", 0.5, "ids_alert:weak")]


def select_resolution(candidates: list[LabelResolution]) -> LabelResolution:
    """Select the highest-priority non-conflicting label resolution."""
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            SOURCE_PRIORITY.get(item.label_source, 50),
            -(item.label_confidence or 0.0),
            item.label_mapping_rule_id or "",
        ),
    )
    best_priority = SOURCE_PRIORITY.get(sorted_candidates[0].label_source, 50)
    best_group = [
        candidate
        for candidate in sorted_candidates
        if SOURCE_PRIORITY.get(candidate.label_source, 50) == best_priority
    ]
    binaries = {candidate.label_binary for candidate in best_group if candidate.label_binary is not None}
    families = {candidate.label_family for candidate in best_group if candidate.label_family is not None}
    if len(binaries) > 1 or len(families) > 1:
        rule_ids = ",".join(filter(None, (candidate.label_mapping_rule_id for candidate in best_group))) or None
        return LabelResolution(None, None, None, best_group[0].label_source, "conflicting_label", 0.0, rule_ids)
    rule_ids = ",".join(filter(None, (candidate.label_mapping_rule_id for candidate in best_group))) or None
    return LabelResolution(
        next(iter(binaries), None),
        next(iter(families), None),
        next((candidate.label_subtype for candidate in best_group if candidate.label_subtype is not None), None),
        best_group[0].label_source,
        best_group[0].label_status,
        max((candidate.label_confidence or 0.0 for candidate in best_group), default=0.0),
        rule_ids,
    )


def rule_matches(rule: LabelRule, row: dict[str, Any], context: ParserContext) -> bool:
    """Return True when a rule matches context and source row fields."""
    if rule.dataset_name_pattern and not pattern_matches(rule.dataset_name_pattern, context.dataset_name):
        return False
    if rule.file_name_pattern:
        source_path = Path(context.source_file_path).as_posix()
        if not pattern_matches(rule.file_name_pattern, source_path) and not pattern_matches(
            rule.file_name_pattern,
            Path(source_path).name,
        ):
            return False
    if rule.source_field:
        value = nested_get(row, rule.source_field)
        if value in ("", None):
            return False
        if rule.source_value_pattern and not pattern_matches(rule.source_value_pattern, str(value)):
            return False
    return True


def resolution_from_value(
    value: Any,
    *,
    source: str,
    status: str,
    confidence: float,
    rule_id: str | None = None,
    subtype: str | None = None,
) -> LabelResolution | None:
    """Map one raw label value into canonical label fields."""
    if isinstance(value, bool):
        return LabelResolution(int(value), None if value else "benign", subtype, source, status, confidence, rule_id)
    if isinstance(value, int) and value in (0, 1):
        return LabelResolution(value, None if value else "benign", subtype, source, status, confidence, rule_id)
    text = str(value).strip().lower()
    if text in UNKNOWN_TOKENS:
        return None
    if text in BENIGN_TOKENS:
        return LabelResolution(0, "benign", subtype, source, status, confidence, rule_id)
    tokens = tokenize_label_text(text)
    for token in tokens:
        family = MALICIOUS_TOKEN_FAMILIES.get(token)
        if family is not None:
            return LabelResolution(
                1,
                None if family == "unknown" else family,
                subtype or (text if text != token else None),
                source,
                status,
                confidence,
                rule_id,
            )
    return None


def load_config_rules(path: Path | None) -> list[LabelRule]:
    """Load label mapping rules from a JSON config file if it exists."""
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("label_mapping_rules", payload if isinstance(payload, list) else [])
    if not isinstance(rows, list):
        raise ValueError(f"label mapping config must contain a list: {path}")
    return [rule_from_mapping(row) for row in rows]


def rule_from_mapping(row: dict[str, Any]) -> LabelRule:
    """Build a LabelRule from config JSON mapping."""
    return LabelRule(
        rule_uid=str(row["rule_uid"]),
        branch=str(row["branch"]),
        role=row.get("role"),
        source_format=row.get("source_format"),
        dataset_name_pattern=row.get("dataset_name_pattern"),
        file_name_pattern=row.get("file_name_pattern"),
        source_field=row.get("source_field"),
        source_value_pattern=row.get("source_value_pattern"),
        label_binary=row.get("label_binary"),
        label_family=row.get("label_family"),
        label_subtype=row.get("label_subtype"),
        label_source=str(row["label_source"]),
        label_status=str(row["label_status"]),
        label_confidence=float(row["label_confidence"]) if row.get("label_confidence") is not None else None,
        priority=int(row.get("priority", 100)),
    )


def rule_from_orm(rule: LabelMappingRule) -> LabelRule:
    """Build a LabelRule from a SQLAlchemy LabelMappingRule instance."""
    confidence = rule.label_confidence
    return LabelRule(
        rule_uid=rule.rule_uid,
        branch=rule.branch,
        role=rule.role,
        source_format=rule.source_format,
        dataset_name_pattern=rule.dataset_name_pattern,
        file_name_pattern=rule.file_name_pattern,
        source_field=rule.source_field,
        source_value_pattern=rule.source_value_pattern,
        label_binary=rule.label_binary,
        label_family=rule.label_family,
        label_subtype=rule.label_subtype,
        label_source=rule.label_source,
        label_status=rule.label_status,
        label_confidence=float(confidence) if isinstance(confidence, Decimal) else confidence,
        priority=rule.priority,
    )


def unlabeled() -> LabelResolution:
    """Return canonical unlabeled fields."""
    return LabelResolution(None, None, None, "none", "unlabeled", None, None)


def first_present(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    """Return the first non-empty nested field value."""
    for field in fields:
        value = nested_get(row, field)
        if value not in ("", None):
            return value
    return None


def nested_get(row: dict[str, Any], dotted_key: str) -> Any:
    """Return a nested value for dotted keys or a flat key fallback."""
    if dotted_key in row:
        return row[dotted_key]
    current: Any = row
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def pattern_matches(pattern: str, value: str) -> bool:
    """Match a regex-like pattern against a value with substring fallback."""
    try:
        return re.search(pattern, value, flags=re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in value.lower()


def tokenize_label_text(value: str) -> list[str]:
    """Tokenize a label-like string for conservative canonical mapping."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    parts = [part for part in normalized.split("_") if part]
    tokens = set(parts)
    tokens.add(normalized)
    return list(tokens)
