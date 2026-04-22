from __future__ import annotations

import csv
import json
import logging
import re
import socket
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BufferedReader
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

try:
    import dpkt
except ImportError:  # pragma: no cover - optional dependency in parser extra
    dpkt = None

try:
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover - optional dependency in parser extra
    pq = None

from cybersec_platform.contracts.api import DatasetFormat, DatasetManifest, FeatureSchemaDefinition, NormalizationProfile, NormalizationSummary

logger = logging.getLogger(__name__)


class ContractValidationError(ValueError):
    pass


class UnsupportedDatasetFormatError(ValueError):
    pass


class NormalizationError(ValueError):
    pass


SUPPORTED_DATASET_FORMATS = {
    ".csv": DatasetFormat.CSV.value,
    ".tsv": DatasetFormat.TSV.value,
    ".parquet": DatasetFormat.PARQUET.value,
    ".xlsx": DatasetFormat.XLSX.value,
    ".json": DatasetFormat.JSON.value,
    ".jsonl": DatasetFormat.JSON.value,
    ".ndjson": DatasetFormat.JSON.value,
    ".pcap": DatasetFormat.PCAP.value,
    ".pcapng": DatasetFormat.PCAP.value,
    ".res": DatasetFormat.RES.value,
    ".sc": DatasetFormat.SC.value,
}

PROFILE_SCHEMA_MAP = {
    NormalizationProfile.DNS2021_TABULAR_FEATURES.value: ["dns-domain-tabular"],
    NormalizationProfile.DNS2021_DOMAIN_LISTS.value: ["dns-domain-intel"],
    NormalizationProfile.DNS_EXF_STATEFUL.value: ["dns-network-stateful"],
    NormalizationProfile.DNS_EXF_STATELESS.value: ["dns-network-stateless"],
    NormalizationProfile.DNS_PCAP_DNS_FLOW.value: ["dns-pcap-flow"],
    NormalizationProfile.GENERIC_TABULAR.value: ["host-simulated"],
    NormalizationProfile.GENERIC_JSON.value: ["host-simulated"],
}

DNS_EXF_STATEFUL_COLUMNS = [
    "rr",
    "a_frequency",
    "ns_frequency",
    "cname_frequency",
    "soa_frequency",
    "null_frequency",
    "ptr_frequency",
    "hinfo_frequency",
    "mx_frequency",
    "txt_frequency",
    "aaaa_frequency",
    "srv_frequency",
    "opt_frequency",
    "rr_type",
    "rr_count",
    "rr_name_entropy",
    "rr_name_length",
    "distinct_ns",
    "distinct_ip",
    "unique_country",
    "unique_asn",
    "distinct_domains",
    "reverse_dns",
    "a_records",
    "unique_ttl",
    "ttl_mean",
    "ttl_variance",
]

DNS_EXF_STATELESS_COLUMNS = [
    "timestamp",
    "fqdn_count",
    "subdomain_length",
    "upper",
    "lower",
    "numeric",
    "entropy",
    "special",
    "labels",
    "labels_max",
    "labels_average",
    "longest_word",
    "sld",
    "len",
    "subdomain",
]

DNS_PCAP_FEATURE_COLUMNS = [
    "packet_count",
    "byte_total",
    "mean_packet_size",
    "mean_inter_arrival_ms",
    "dns_query_entropy_mean",
    "communication_frequency",
    "query_rr_count",
    "answer_rr_count",
    "unique_qnames",
    "rr_type_a",
    "rr_type_ns",
    "rr_type_cname",
    "rr_type_mx",
    "rr_type_txt",
    "rr_type_aaaa",
    "rr_type_ptr",
    "rr_type_other",
    "ttl_mean",
    "ttl_max",
]

DOMAIN_INTEL_COLUMNS = [
    "domain_length",
    "numeric_ratio",
    "subdomain_depth",
    "domain_entropy",
    "hyphen_count",
]

CORE_EVENT_COLUMNS = ["entity_id", "event_ts", "source_type", "label", "attack_stage", "mitre_tactic"]
SYSTEM_CALL_KV_PATTERN = re.compile(r"(?:^|\s)([A-Za-z_][A-Za-z0-9_]*)=(.*?)(?=(?:\s+[A-Za-z_][A-Za-z0-9_]*=)|$)")


def ensure_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ContractValidationError(f"Dataset is missing required columns: {missing}")


def detect_dataset_format(path: str | Path) -> str:
    target = Path(path)
    extension = target.suffix.lower()
    dataset_format = SUPPORTED_DATASET_FORMATS.get(extension)
    if dataset_format is None and target.exists():
        with target.open("rb") as file:
            header = file.read(4)
        if header in {b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4", b"\x0a\x0d\x0d\x0a"}:
            return DatasetFormat.PCAP.value
    if dataset_format is None:
        raise UnsupportedDatasetFormatError(f"Unsupported dataset format: {extension or 'unknown'}")
    return dataset_format


def _safe_json_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(list(value) if isinstance(value, set) else value, ensure_ascii=False, default=str)
    return str(value)


def _normalize_column_name(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_").lower()
    return normalized or "unnamed"


def _domain_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * __import__("math").log2(probability)
    return float(entropy)


def _filename_to_label(path: Path) -> int:
    lowered = path.name.lower()
    return 0 if "benign" in lowered else 1


def _filename_to_attack_stage(path: Path) -> str | None:
    lowered = path.name.lower()
    if "benign" in lowered:
        return None
    if any(token in lowered for token in ("phishing", "malware", "spam", "heavy", "light", "attack", "exf")):
        return "exfiltration"
    return "suspicious_activity"


def _default_label(manifest: DatasetManifest, path: Path) -> int:
    if manifest.default_label is not None:
        return int(manifest.default_label)
    return _filename_to_label(path)


def _default_attack_stage(manifest: DatasetManifest, path: Path) -> str | None:
    if manifest.default_attack_stage is not None:
        return manifest.default_attack_stage
    return _filename_to_attack_stage(path)


def _default_mitre_tactic(source_type: str) -> str | None:
    return "TA0011" if source_type == "network" else "TA0006"


def _detect_delimiter(path: Path, dataset_format: str) -> str:
    if dataset_format == DatasetFormat.TSV.value:
        return "\t"
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
    if not sample:
        raise ContractValidationError("Dataset file is empty")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        return ","


def _is_domain_list_path(path: Path) -> bool:
    lowered = path.name.lower()
    return lowered.endswith("_domains.csv") or lowered.endswith("_domains.tsv")


def _read_domain_list_lines(path: Path) -> pd.DataFrame:
    values: list[str] = []
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            if "," in line:
                token = next((item.strip() for item in line.split(",") if item.strip()), "")
            else:
                token = line
            values.append(token)
    return pd.DataFrame({"domain": values})


def _read_json_records(path: Path) -> pd.DataFrame:
    content = path.read_text(encoding="utf-8")
    stripped = content.lstrip()
    if not stripped:
        raise ContractValidationError("Dataset file is empty")
    if stripped[0] == "[":
        payload = json.loads(content)
        if not isinstance(payload, list):
            raise ContractValidationError("JSON dataset must contain a list of records")
        return pd.json_normalize(payload)
    if stripped[0] == "{":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ContractValidationError("JSON dataset must contain an object record")
        return pd.json_normalize([payload])
    records: list[dict[str, Any]] = []
    for index, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ContractValidationError(f"JSON line {index} is not an object record")
        records.append(item)
    return pd.json_normalize(records)


def _coerce_epoch_unit(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 1e17:
        return "ns"
    if magnitude >= 1e14:
        return "us"
    if magnitude >= 1e11:
        return "ms"
    return "s"


def _coerce_trace_scalar(value: str) -> Any:
    cleaned = value.strip()
    if not cleaned:
        return None
    if re.fullmatch(r"-?\d+", cleaned):
        return int(cleaned)
    if re.fullmatch(r"-?\d+\.\d+", cleaned):
        return float(cleaned)
    return cleaned


def _trace_event_timestamp(value: str) -> str | None:
    try:
        numeric_value = float(value)
    except ValueError:
        return None
    unit = _coerce_epoch_unit(numeric_value)
    divisor_map = {"s": 1.0, "ms": 1_000.0, "us": 1_000_000.0, "ns": 1_000_000_000.0}
    return datetime.fromtimestamp(numeric_value / divisor_map[unit], tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_system_call_record(line: str) -> dict[str, Any] | None:
    parts = line.strip().split(None, 7)
    if len(parts) < 7:
        return None

    timestamp_raw, cpu_raw, thread_raw, process_name, process_raw, syscall_name, direction = parts[:7]
    remainder = parts[7].strip() if len(parts) > 7 else ""
    process_id = _coerce_trace_scalar(process_raw)
    entity_token = process_raw if process_raw else str(thread_raw)
    record: dict[str, Any] = {
        "timestamp_ns": _coerce_trace_scalar(timestamp_raw),
        "cpu_id": _coerce_trace_scalar(cpu_raw),
        "thread_id": _coerce_trace_scalar(thread_raw),
        "process_name": process_name,
        "process_id": process_id,
        "syscall": syscall_name,
        "direction": direction,
        "event_ts": _trace_event_timestamp(timestamp_raw),
        "entity_id": f"{process_name}:{entity_token}",
        "raw_args": remainder or None,
    }
    for match in SYSTEM_CALL_KV_PATTERN.finditer(remainder):
        key = _normalize_column_name(match.group(1))
        record[key] = _coerce_trace_scalar(match.group(2))
    return record


def iter_system_call_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", errors="ignore") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            parsed = _parse_system_call_record(line)
            if parsed is not None:
                yield parsed


def load_system_call_frame(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row_index, record in enumerate(iter_system_call_records(path), start=1):
        rows.append(record)
        if max_rows is not None and row_index >= max_rows:
            break
    if not rows:
        raise ContractValidationError("System call trace is empty after parsing")
    return pd.DataFrame(rows)


def read_dataset_headers(path: str | Path) -> list[str]:
    target = Path(path)
    dataset_format = detect_dataset_format(target)
    profile = infer_normalization_profile(target, dataset_format, None)
    try:
        if dataset_format in {DatasetFormat.CSV.value, DatasetFormat.TSV.value, DatasetFormat.RES.value}:
            if profile == NormalizationProfile.DNS2021_DOMAIN_LISTS.value:
                return ["domain"]
            delimiter = _detect_delimiter(target, dataset_format)
            frame = pd.read_csv(target, sep=delimiter, nrows=0, engine="python", on_bad_lines="skip")
            return [_normalize_column_name(str(column)) for column in frame.columns]
        if dataset_format == DatasetFormat.PARQUET.value:
            if pq is None:
                raise UnsupportedDatasetFormatError("Parquet support is not installed")
            return [_normalize_column_name(name) for name in pq.ParquetFile(target).schema_arrow.names]
        if dataset_format == DatasetFormat.XLSX.value:
            frame = pd.read_excel(target, nrows=0)
            return [_normalize_column_name(str(column)) for column in frame.columns]
        if dataset_format == DatasetFormat.JSON.value:
            frame = _read_json_records(target).head(0)
            return [_normalize_column_name(str(column)) for column in frame.columns]
        if dataset_format == DatasetFormat.PCAP.value:
            return DNS_PCAP_FEATURE_COLUMNS.copy()
        if dataset_format == DatasetFormat.SC.value:
            frame = load_system_call_frame(target, max_rows=200).head(0)
            return [_normalize_column_name(str(column)) for column in frame.columns]
    except UnsupportedDatasetFormatError:
        raise
    except Exception as exc:  # pragma: no cover - exercised by API tests
        raise ContractValidationError(f"Unable to read dataset headers: {exc}") from exc
    raise UnsupportedDatasetFormatError(f"Unsupported dataset format: {target.suffix.lower() or 'unknown'}")


def load_dataset_frame(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    target = Path(path)
    dataset_format = detect_dataset_format(target)
    line_count = None
    if dataset_format in {DatasetFormat.CSV.value, DatasetFormat.TSV.value, DatasetFormat.RES.value, DatasetFormat.JSON.value, DatasetFormat.SC.value}:
        try:
            line_count = sum(1 for _ in target.open("r", encoding="utf-8-sig", errors="ignore"))
        except OSError:
            line_count = None
    try:
        if dataset_format in {DatasetFormat.CSV.value, DatasetFormat.TSV.value, DatasetFormat.RES.value}:
            if _is_domain_list_path(target):
                return _read_domain_list_lines(target), {"source_line_count": line_count, "skipped_rows_estimate": 0}
            delimiter = _detect_delimiter(target, dataset_format)
            frame = pd.read_csv(target, sep=delimiter, engine="python", on_bad_lines="skip")
            skipped_rows = max((line_count or len(frame) + 1) - (len(frame) + 1), 0)
            return frame, {"source_line_count": line_count, "skipped_rows_estimate": skipped_rows}
        if dataset_format == DatasetFormat.PARQUET.value:
            return pd.read_parquet(target), {"source_line_count": None, "skipped_rows_estimate": 0}
        if dataset_format == DatasetFormat.XLSX.value:
            return pd.read_excel(target), {"source_line_count": None, "skipped_rows_estimate": 0}
        if dataset_format == DatasetFormat.JSON.value:
            return _read_json_records(target), {"source_line_count": line_count, "skipped_rows_estimate": 0}
        if dataset_format == DatasetFormat.SC.value:
            frame = load_system_call_frame(target)
            skipped_rows = max((line_count or len(frame)) - len(frame), 0)
            return frame, {"source_line_count": line_count, "skipped_rows_estimate": skipped_rows}
    except UnsupportedDatasetFormatError:
        raise
    except Exception as exc:  # pragma: no cover - exercised by worker/api tests
        raise ContractValidationError(f"Unable to load dataset file: {exc}") from exc
    raise UnsupportedDatasetFormatError(f"Unsupported dataset format: {target.suffix.lower() or 'unknown'}")


def infer_normalization_profile(path: Path, dataset_format: str, columns: list[str] | None) -> str:
    lowered_name = path.name.lower()
    normalized_columns = [_normalize_column_name(column) for column in columns or []]
    if dataset_format == DatasetFormat.PCAP.value:
        return NormalizationProfile.DNS_PCAP_DNS_FLOW.value
    if _is_domain_list_path(path):
        return NormalizationProfile.DNS2021_DOMAIN_LISTS.value
    if dataset_format == DatasetFormat.JSON.value:
        return NormalizationProfile.GENERIC_JSON.value
    if normalized_columns == DNS_EXF_STATEFUL_COLUMNS:
        return NormalizationProfile.DNS_EXF_STATEFUL.value
    if normalized_columns == DNS_EXF_STATELESS_COLUMNS:
        return NormalizationProfile.DNS_EXF_STATELESS.value
    if {"domain", "ttl", "asn", "ip", "entropy"} <= set(normalized_columns) or lowered_name.startswith("csv_"):
        return NormalizationProfile.DNS2021_TABULAR_FEATURES.value
    return NormalizationProfile.GENERIC_TABULAR.value


@dataclass
class NormalizationInspection:
    relative_path: str
    dataset_format: str
    normalization_profile: str
    columns: list[str]
    suggested_name: str
    target_columns: list[str]
    quality_warnings: list[str]
    supporting_only: bool
    compatible_feature_schemas: list[str]


@dataclass
class NormalizationOutput:
    normalized_path: str
    row_count: int
    columns: list[str]
    detected_format: str
    normalization_profile: str
    normalization_summary: dict[str, Any]
    normalization_report_path: str | None


def inspect_dataset_source(path: str | Path) -> NormalizationInspection:
    target = Path(path)
    dataset_format = detect_dataset_format(target)
    columns = read_dataset_headers(target)
    profile = infer_normalization_profile(target, dataset_format, columns)
    warnings: list[str] = []
    supporting_only = profile == NormalizationProfile.DNS2021_DOMAIN_LISTS.value
    if supporting_only:
        warnings.append("Domain list source is supporting_only and not directly train-ready.")
    if dataset_format == DatasetFormat.PCAP.value:
        warnings.append("PCAP normalization is streaming and may take significant time on large files.")
    if dataset_format == DatasetFormat.SC.value:
        warnings.append("System call traces are parsed heuristically; malformed lines are skipped during normalization.")
    if profile == NormalizationProfile.DNS2021_TABULAR_FEATURES.value:
        warnings.append("DNS-2021 CSV files are heterogeneous; malformed rows will be skipped and reported.")
    target_columns = target_schema_columns_for_profile(profile)
    return NormalizationInspection(
        relative_path=target.name,
        dataset_format=dataset_format,
        normalization_profile=profile,
        columns=columns,
        suggested_name=f"{target.stem}-dataset",
        target_columns=target_columns,
        quality_warnings=warnings,
        supporting_only=supporting_only,
        compatible_feature_schemas=PROFILE_SCHEMA_MAP.get(profile, []),
    )


def target_schema_columns_for_profile(profile: str) -> list[str]:
    profile_map = {
        NormalizationProfile.DNS_EXF_STATEFUL.value: CORE_EVENT_COLUMNS + DNS_EXF_STATEFUL_COLUMNS,
        NormalizationProfile.DNS_EXF_STATELESS.value: CORE_EVENT_COLUMNS + [item for item in DNS_EXF_STATELESS_COLUMNS if item != "timestamp"],
        NormalizationProfile.DNS2021_DOMAIN_LISTS.value: CORE_EVENT_COLUMNS + DOMAIN_INTEL_COLUMNS,
        NormalizationProfile.DNS_PCAP_DNS_FLOW.value: CORE_EVENT_COLUMNS + DNS_PCAP_FEATURE_COLUMNS,
    }
    return profile_map.get(profile, CORE_EVENT_COLUMNS.copy())


def _safe_datetime_series(series: pd.Series) -> pd.Series:
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns, UTC]")
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_mask = numeric.notna()
    if numeric_mask.any():
        unit = _coerce_epoch_unit(float(numeric[numeric_mask].abs().max()))
        parsed.loc[numeric_mask] = pd.to_datetime(numeric[numeric_mask], errors="coerce", unit=unit, utc=True)
    text_mask = parsed.isna() & series.notna()
    if text_mask.any():
        parsed.loc[text_mask] = pd.to_datetime(series[text_mask], errors="coerce", utc=True)
    return parsed


def _synthetic_timestamps(length: int, base: datetime | None = None) -> pd.Series:
    anchor = base or datetime(2026, 1, 1, tzinfo=UTC)
    return pd.Series([anchor + timedelta(seconds=index) for index in range(length)])


def _coerce_numeric_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    invalid_values = 0
    for column in frame.columns:
        if frame[column].dtype != "object":
            continue
        flattened = frame[column].map(_safe_json_value)
        converted = pd.to_numeric(flattened, errors="coerce")
        numeric_candidates = converted.notna().sum()
        if numeric_candidates >= max(1, int(len(frame) * 0.6)):
            invalid_values += int(flattened.notna().sum() - converted.notna().sum())
            frame[column] = converted
        else:
            frame[column] = flattened
    return frame, invalid_values


def _build_domain_features(domains: Iterable[str]) -> pd.DataFrame:
    rows = []
    for domain in domains:
        cleaned = str(domain).strip().strip('"').strip("'").lower()
        if not cleaned:
            continue
        labels = [item for item in cleaned.split(".") if item]
        rows.append(
            {
                "domain_value": cleaned,
                "domain_length": len(cleaned),
                "numeric_ratio": sum(char.isdigit() for char in cleaned) / max(len(cleaned), 1),
                "subdomain_depth": max(len(labels) - 2, 0),
                "domain_entropy": _domain_entropy(cleaned),
                "hyphen_count": cleaned.count("-"),
            }
        )
    return pd.DataFrame(rows)


def _normalize_domain_list(path: Path, manifest: DatasetManifest) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = _read_domain_list_lines(path)
    feature_frame = _build_domain_features(frame["domain"].tolist())
    if feature_frame.empty:
        raise ContractValidationError("Domain list dataset is empty after parsing")
    event_ts = _synthetic_timestamps(len(feature_frame))
    normalized = pd.DataFrame(
        {
            "entity_id": feature_frame["domain_value"],
            "event_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_type": manifest.source_type.value,
            "label": _default_label(manifest, path),
            "attack_stage": _default_attack_stage(manifest, path),
            "mitre_tactic": _default_mitre_tactic(manifest.source_type.value),
        }
    )
    for column in DOMAIN_INTEL_COLUMNS:
        normalized[column] = feature_frame[column]
    summary = {
        "supporting_only": True,
        "warnings": ["Domain lists are treated as auxiliary supporting_only inputs."],
        "profile_details": {"domain_count": len(feature_frame)},
    }
    return normalized, summary


def _normalize_tabular(
    raw_frame: pd.DataFrame,
    path: Path,
    manifest: DatasetManifest,
    profile: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = raw_frame.copy()
    frame.columns = [_normalize_column_name(str(column)) for column in frame.columns]
    original_columns = list(frame.columns)
    duplicates_before = int(frame.duplicated().sum())
    if duplicates_before:
        frame = frame.drop_duplicates().reset_index(drop=True)

    metadata_columns = {
        "entity_id",
        "event_ts",
        "label",
        "attack_stage",
        "mitre_tactic",
        "source_type",
    }
    event_ts_column = _normalize_column_name(manifest.timestamp_column)
    entity_column = _normalize_column_name(manifest.entity_id_column)
    label_column = _normalize_column_name(manifest.label_column)
    attack_stage_column = _normalize_column_name(manifest.attack_stage_column or "attack_stage")

    if entity_column in frame.columns:
        entity_id = frame[entity_column].map(_safe_json_value)
    elif "domain" in frame.columns:
        entity_id = frame["domain"].map(_safe_json_value)
    elif "domain_name" in frame.columns:
        entity_id = frame["domain_name"].map(_safe_json_value)
    elif "rr" in frame.columns:
        entity_id = frame["rr"].map(_safe_json_value)
    else:
        entity_id = pd.Series([f"{path.stem}-{index}" for index in range(len(frame))])

    if event_ts_column in frame.columns:
        timestamps = _safe_datetime_series(frame[event_ts_column])
    elif "timestamp" in frame.columns:
        timestamps = _safe_datetime_series(frame["timestamp"])
    else:
        timestamps = _synthetic_timestamps(len(frame))
    synthetic_timestamps_used = int(timestamps.isna().sum())
    if synthetic_timestamps_used:
        fallback = _synthetic_timestamps(len(frame))
        timestamps = timestamps.fillna(fallback)

    if label_column in frame.columns:
        labels = pd.to_numeric(frame[label_column], errors="coerce").fillna(_default_label(manifest, path)).astype(int)
    else:
        labels = pd.Series([_default_label(manifest, path)] * len(frame))

    if attack_stage_column in frame.columns:
        attack_stage = frame[attack_stage_column].map(_safe_json_value)
    else:
        attack_stage = pd.Series([_default_attack_stage(manifest, path)] * len(frame))

    if "mitre_tactic" in frame.columns:
        mitre_tactic = frame["mitre_tactic"].map(_safe_json_value)
    else:
        mitre_tactic = pd.Series([_default_mitre_tactic(manifest.source_type.value)] * len(frame))

    normalized = pd.DataFrame(
        {
            "entity_id": entity_id.ffill().fillna(f"{path.stem}-entity"),
            "event_ts": pd.to_datetime(timestamps, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_type": manifest.source_type.value,
            "label": labels,
            "attack_stage": attack_stage,
            "mitre_tactic": mitre_tactic,
        }
    )

    feature_frame = frame.drop(columns=[column for column in frame.columns if column in {entity_column, event_ts_column, label_column, attack_stage_column}], errors="ignore")
    feature_frame, invalid_values = _coerce_numeric_features(feature_frame)
    for column in feature_frame.columns:
        if column in metadata_columns:
            continue
        normalized[column] = feature_frame[column]

    summary = {
        "supporting_only": False,
        "warnings": [],
        "profile_details": {
            "original_columns": original_columns,
            "synthetic_timestamps_used": synthetic_timestamps_used,
        },
        "duplicate_rows": duplicates_before,
        "invalid_values": invalid_values,
    }
    if synthetic_timestamps_used or event_ts_column not in frame.columns:
        summary["warnings"].append("Synthetic timestamps were used for rows without a parseable event timestamp.")
    if label_column not in frame.columns:
        summary["warnings"].append("Labels were derived deterministically from the file name.")
    if profile == NormalizationProfile.DNS2021_TABULAR_FEATURES.value:
        summary["warnings"].append("DNS-2021 tabular files may contain malformed rows; tolerant parsing was applied.")
    return normalized, summary


def _infer_rr_type_name(record_type: int) -> str:
    mapping = {
        dpkt.dns.DNS_A: "a",
        dpkt.dns.DNS_NS: "ns",
        dpkt.dns.DNS_CNAME: "cname",
        dpkt.dns.DNS_MX: "mx",
        dpkt.dns.DNS_TXT: "txt",
        dpkt.dns.DNS_AAAA: "aaaa",
        dpkt.dns.DNS_PTR: "ptr",
    }
    return mapping.get(record_type, "other")


def _ip_to_text(value: bytes) -> str:
    if len(value) == 4:
        return socket.inet_ntop(socket.AF_INET, value)
    if len(value) == 16:
        return socket.inet_ntop(socket.AF_INET6, value)
    return "unknown"


def _pcap_reader(file: BufferedReader):
    if dpkt is None:
        raise UnsupportedDatasetFormatError("PCAP support is not installed")
    header = file.peek(4)[:4]
    if header == b"\x0a\x0d\x0d\x0a":
        return dpkt.pcapng.Reader(file)
    return dpkt.pcap.Reader(file)


def _normalize_pcap(path: Path, manifest: DatasetManifest) -> tuple[pd.DataFrame, dict[str, Any]]:
    if dpkt is None:
        raise UnsupportedDatasetFormatError("PCAP support is not installed")

    buckets: dict[tuple[str, str, int], dict[str, Any]] = {}
    with path.open("rb") as file:
        reader = _pcap_reader(file)  # type: ignore[arg-type]
        for ts, buf in reader:
            try:
                ethernet = dpkt.ethernet.Ethernet(buf)
                ip = ethernet.data
                if not hasattr(ip, "data"):
                    continue
                transport = ip.data
                if not isinstance(transport, dpkt.udp.UDP):
                    continue
                if transport.sport != 53 and transport.dport != 53:
                    continue
                dns = dpkt.dns.DNS(transport.data)
            except (dpkt.dpkt.NeedData, dpkt.dpkt.UnpackError, ValueError):
                continue

            src_ip = _ip_to_text(ip.src)
            dst_ip = _ip_to_text(ip.dst)
            second_bucket = int(ts)
            key = (src_ip, dst_ip, second_bucket)
            bucket = buckets.setdefault(
                key,
                {
                    "packet_count": 0,
                    "byte_total": 0,
                    "packet_sizes": [],
                    "timestamps": [],
                    "qnames": set(),
                    "query_rr_count": 0,
                    "answer_rr_count": 0,
                    "rr_type_counts": Counter(),
                    "ttl_values": [],
                },
            )
            bucket["packet_count"] += 1
            bucket["byte_total"] += len(buf)
            bucket["packet_sizes"].append(len(buf))
            bucket["timestamps"].append(ts)
            for question in dns.qd:
                qname = getattr(question, "name", None)
                if qname:
                    bucket["qnames"].add(str(qname))
                    bucket["query_rr_count"] += 1
            for answer in dns.an:
                bucket["answer_rr_count"] += 1
                bucket["rr_type_counts"][_infer_rr_type_name(answer.type)] += 1
                ttl = getattr(answer, "ttl", None)
                if ttl is not None:
                    bucket["ttl_values"].append(ttl)

    rows: list[dict[str, Any]] = []
    for (src_ip, dst_ip, second_bucket), payload in sorted(buckets.items(), key=lambda item: item[0][2]):
        if payload["packet_count"] == 0:
            continue
        timestamps = sorted(payload["timestamps"])
        inter_arrivals = [
            (current - previous) * 1000.0 for previous, current in zip(timestamps, timestamps[1:], strict=False) if current >= previous
        ]
        qname_entropy_values = [_domain_entropy(value) for value in payload["qnames"]]
        ttl_values = payload["ttl_values"] or [0]
        rows.append(
            {
                "entity_id": f"{src_ip}->{dst_ip}",
                "event_ts": datetime.fromtimestamp(second_bucket, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_type": manifest.source_type.value,
                "label": _default_label(manifest, path),
                "attack_stage": _default_attack_stage(manifest, path),
                "mitre_tactic": _default_mitre_tactic(manifest.source_type.value),
                "packet_count": payload["packet_count"],
                "byte_total": payload["byte_total"],
                "mean_packet_size": float(sum(payload["packet_sizes"]) / len(payload["packet_sizes"])),
                "mean_inter_arrival_ms": float(sum(inter_arrivals) / len(inter_arrivals)) if inter_arrivals else 0.0,
                "dns_query_entropy_mean": float(sum(qname_entropy_values) / len(qname_entropy_values)) if qname_entropy_values else 0.0,
                "communication_frequency": payload["packet_count"],
                "query_rr_count": payload["query_rr_count"],
                "answer_rr_count": payload["answer_rr_count"],
                "unique_qnames": len(payload["qnames"]),
                "rr_type_a": payload["rr_type_counts"].get("a", 0),
                "rr_type_ns": payload["rr_type_counts"].get("ns", 0),
                "rr_type_cname": payload["rr_type_counts"].get("cname", 0),
                "rr_type_mx": payload["rr_type_counts"].get("mx", 0),
                "rr_type_txt": payload["rr_type_counts"].get("txt", 0),
                "rr_type_aaaa": payload["rr_type_counts"].get("aaaa", 0),
                "rr_type_ptr": payload["rr_type_counts"].get("ptr", 0),
                "rr_type_other": payload["rr_type_counts"].get("other", 0),
                "ttl_mean": float(sum(ttl_values) / len(ttl_values)),
                "ttl_max": max(ttl_values),
            }
        )

    if not rows:
        raise ContractValidationError("PCAP file did not yield any DNS flow records")

    normalized = pd.DataFrame(rows)
    summary = {
        "supporting_only": False,
        "warnings": ["PCAP was normalized through streaming DNS flow aggregation."],
        "profile_details": {"bucket_count": len(rows)},
    }
    return normalized, summary


def _apply_feature_schema(
    normalized: pd.DataFrame,
    feature_schema: FeatureSchemaDefinition | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if feature_schema is None:
        return normalized, {"schema_name": None, "selected_features": []}

    required_columns = [column for column in feature_schema.required_columns if column in normalized.columns]
    missing_columns = [column for column in feature_schema.required_columns if column not in normalized.columns]
    if missing_columns:
        raise ContractValidationError(f"Normalized dataset is missing FeatureSchema required columns: {missing_columns}")

    selected_columns = CORE_EVENT_COLUMNS + required_columns
    return normalized[selected_columns], {
        "schema_name": feature_schema.name,
        "schema_version": feature_schema.version,
        "selected_features": required_columns,
        "feature_families": [item.value for item in feature_schema.feature_families],
    }


class NormalizationEngine:
    def validate_and_normalize(
        self,
        raw_path: str,
        manifest: DatasetManifest,
        output_path: str,
        report_path: str | None = None,
        feature_schema: FeatureSchemaDefinition | None = None,
    ) -> NormalizationOutput:
        target = Path(raw_path)
        dataset_format = detect_dataset_format(target)
        header_columns = read_dataset_headers(target)
        profile = infer_normalization_profile(target, dataset_format, header_columns)

        if dataset_format == DatasetFormat.PCAP.value:
            normalized, summary = _normalize_pcap(target, manifest)
            load_meta = {"skipped_rows_estimate": 0}
        elif profile == NormalizationProfile.DNS2021_DOMAIN_LISTS.value:
            normalized, summary = _normalize_domain_list(target, manifest)
            load_meta = {"skipped_rows_estimate": 0}
        else:
            frame, load_meta = load_dataset_frame(target)
            normalized, summary = _normalize_tabular(frame, target, manifest, profile)

        normalized.columns = [_normalize_column_name(str(column)) for column in normalized.columns]
        missing_values = int(normalized.isna().sum().sum())
        duplicate_rows = int(normalized.duplicated().sum())
        if duplicate_rows:
            normalized = normalized.drop_duplicates().reset_index(drop=True)
        selected_frame, schema_details = _apply_feature_schema(normalized, feature_schema)

        normalized_summary = NormalizationSummary(
            row_count=len(selected_frame),
            dropped_rows=int(load_meta.get("skipped_rows_estimate", 0)),
            duplicate_rows=duplicate_rows + int(summary.get("duplicate_rows", 0)),
            missing_values=missing_values,
            invalid_values=int(summary.get("invalid_values", 0)),
            supporting_only=bool(summary.get("supporting_only", False)),
            warnings=list(dict.fromkeys(summary.get("warnings", []))),
            profile_details={
                "detected_format": dataset_format,
                "normalization_profile": profile,
                **summary.get("profile_details", {}),
                **schema_details,
            },
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        selected_frame.to_csv(output_path, index=False)

        report_payload = {
            "raw_path": str(target),
            "normalized_path": output_path,
            "detected_format": dataset_format,
            "normalization_profile": profile,
            "columns": list(selected_frame.columns),
            "quality_summary": normalized_summary.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json"),
        }
        if report_path:
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            Path(report_path).write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

        logger.info(
            "Normalized dataset",
            extra={
                "raw_path": str(target),
                "detected_format": dataset_format,
                "normalization_profile": profile,
                "row_count": len(selected_frame),
            },
        )
        return NormalizationOutput(
            normalized_path=output_path,
            row_count=len(selected_frame),
            columns=list(selected_frame.columns),
            detected_format=dataset_format,
            normalization_profile=profile,
            normalization_summary=normalized_summary.model_dump(mode="json"),
            normalization_report_path=report_path,
        )
