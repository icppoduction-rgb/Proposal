from __future__ import annotations

import bz2
import gzip
import json
import lzma
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd

from cybersec_platform.contracts.api import FeatureFamily, FeatureSchemaDefinition, SourceType
from cybersec_platform.ml.normalization import detect_dataset_format, inspect_dataset_source

CORE_EVENT_COLUMNS = ["entity_id", "event_ts", "source_type", "label", "attack_stage", "mitre_tactic"]

SUPPORTED_ARCHIVE_FORMATS = (
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tgz",
    ".tbz2",
    ".txz",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
)
_HOST_DATASET_EXTENSIONS = {".sc", ".res"}
_NETWORK_DATASET_EXTENSIONS = {".csv", ".tsv", ".parquet", ".xlsx", ".pcap", ".pcapng"}
_SIDECAR_METADATA_KEYS = {"container", "exploit", "exploit_name", "image", "recording_time", "time"}
_HIGH_CARDINALITY_COLUMNS = {
    "args",
    "cgroups",
    "cmd",
    "cwd",
    "data",
    "filename",
    "name",
    "path",
    "raw_args",
    "request",
    "tuple",
    "val",
}


class ArchiveExtractionError(ValueError):
    pass


@dataclass
class AutoTrainingInputFile:
    archive_name: str
    extracted_path: str
    relative_path: str
    dataset_format: str
    normalization_profile: str
    source_type: SourceType
    default_label: int | None
    default_attack_stage: str | None
    quality_warnings: list[str]


@dataclass
class AutoTrainingDiscoveryResult:
    source_type: SourceType | None
    metadata: dict[str, Any]
    trainable_files: list[AutoTrainingInputFile]
    skipped_files: list[dict[str, str]]


def detect_archive_format(path: str | Path) -> str:
    target = Path(path)
    lowered_name = target.name.lower()
    for suffix in SUPPORTED_ARCHIVE_FORMATS:
        if lowered_name.endswith(suffix):
            return suffix.lstrip(".")
    raise ArchiveExtractionError(f"Unsupported archive format: {target.suffix.lower() or 'unknown'}")


def is_supported_archive_path(path: str | Path) -> bool:
    try:
        detect_archive_format(path)
    except ArchiveExtractionError:
        return False
    return True


def extract_archive(path: str | Path, destination: str | Path) -> list[Path]:
    archive_path = Path(path)
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    archive_format = detect_archive_format(archive_path)

    if archive_format == "zip":
        return _extract_zip_archive(archive_path, destination_path)
    if archive_format in {"tar", "tar.gz", "tar.bz2", "tar.xz", "tgz", "tbz2", "txz"}:
        return _extract_tar_archive(archive_path, destination_path)
    if archive_format in {"gz", "bz2", "xz"}:
        return [_extract_single_file_archive(archive_path, destination_path, archive_format)]
    raise ArchiveExtractionError(f"Unsupported archive format: {archive_format}")


def discover_archive_training_inputs(extracted_root: str | Path, archive_name: str, archive_path: str | Path) -> AutoTrainingDiscoveryResult:
    root = Path(extracted_root)
    metadata_payload, metadata_path = _load_archive_metadata(root)
    discovered_files = [path for path in sorted(root.rglob("*")) if path.is_file()]
    preferred_source_type = _infer_archive_source_type(discovered_files, archive_path)
    default_label = _label_from_metadata(metadata_payload)
    default_attack_stage = _attack_stage_from_metadata(metadata_payload, default_label)

    trainable_files: list[AutoTrainingInputFile] = []
    skipped_files: list[dict[str, str]] = []
    for path in discovered_files:
        try:
            dataset_format = detect_dataset_format(path)
        except Exception:
            skipped_files.append({"path": path.relative_to(root).as_posix(), "reason": "unsupported_dataset_format"})
            continue

        if metadata_path is not None and path.resolve() == metadata_path.resolve():
            skipped_files.append({"path": path.relative_to(root).as_posix(), "reason": "archive_metadata"})
            continue

        try:
            inspection = inspect_dataset_source(path)
        except Exception as exc:
            skipped_files.append({"path": path.relative_to(root).as_posix(), "reason": str(exc)})
            continue

        source_type = _infer_dataset_source_type(path, preferred_source_type, archive_path)
        if preferred_source_type is not None and source_type != preferred_source_type:
            skipped_files.append({"path": path.relative_to(root).as_posix(), "reason": f"ignored_for_{preferred_source_type.value}"})
            continue
        if inspection.supporting_only:
            skipped_files.append({"path": path.relative_to(root).as_posix(), "reason": "supporting_only"})
            continue

        trainable_files.append(
            AutoTrainingInputFile(
                archive_name=archive_name,
                extracted_path=str(path.resolve()),
                relative_path=path.relative_to(root).as_posix(),
                dataset_format=dataset_format,
                normalization_profile=inspection.normalization_profile,
                source_type=source_type,
                default_label=default_label,
                default_attack_stage=default_attack_stage,
                quality_warnings=inspection.quality_warnings,
            )
        )

    if preferred_source_type is None and trainable_files:
        preferred_source_type = trainable_files[0].source_type

    return AutoTrainingDiscoveryResult(
        source_type=preferred_source_type,
        metadata=metadata_payload,
        trainable_files=trainable_files,
        skipped_files=skipped_files,
    )


def build_auto_feature_schema_definition(
    frame: pd.DataFrame,
    source_type: SourceType,
    *,
    name: str,
    version: str = "1.0.0",
    max_features: int = 128,
) -> FeatureSchemaDefinition:
    selected_columns = _select_feature_columns(frame, max_features=max_features)
    if not selected_columns:
        raise ArchiveExtractionError("Automatic feature selection did not yield any usable columns")

    feature_families = _infer_feature_families(selected_columns, source_type)
    return FeatureSchemaDefinition(
        name=name,
        version=version,
        source_type=source_type,
        required_columns=selected_columns,
        canonical_mappings={"event_ts": "event_ts", "entity_id": "entity_id"},
        feature_families=feature_families,
        notes="Automatically generated from uploaded archives.",
    )


def _safe_member_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/").strip("/")
    if not normalized:
        raise ArchiveExtractionError("Archive member path is empty")
    posix_path = PurePosixPath(normalized)
    if posix_path.is_absolute() or any(part in {"", ".", ".."} for part in posix_path.parts):
        raise ArchiveExtractionError(f"Unsafe archive member path: {member_name}")
    target = (root / Path(posix_path.as_posix())).resolve()
    root_resolved = root.resolve()
    if not target.is_relative_to(root_resolved):
        raise ArchiveExtractionError(f"Archive member path escapes destination: {member_name}")
    return target


def _extract_zip_archive(path: Path, destination: Path) -> list[Path]:
    extracted_files: list[Path] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = _safe_member_path(destination, member.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted_files.append(target)
    return extracted_files


def _extract_tar_archive(path: Path, destination: Path) -> list[Path]:
    extracted_files: list[Path] = []
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            target = _safe_member_path(destination, member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted_files.append(target)
    return extracted_files


def _extract_single_file_archive(path: Path, destination: Path, archive_format: str) -> Path:
    output_name = _single_file_archive_name(path, archive_format)
    target = _safe_member_path(destination, output_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    opener = {
        "gz": gzip.open,
        "bz2": bz2.open,
        "xz": lzma.open,
    }[archive_format]
    with opener(path, "rb") as source, target.open("wb") as output:
        shutil.copyfileobj(source, output)
    return target


def _single_file_archive_name(path: Path, archive_format: str) -> str:
    suffix = f".{archive_format}"
    lowered_name = path.name.lower()
    if not lowered_name.endswith(suffix):
        raise ArchiveExtractionError(f"Unsupported single-file archive name: {path.name}")
    return path.name[: -len(suffix)]


def _load_archive_metadata(root: Path) -> tuple[dict[str, Any], Path | None]:
    for path in sorted(root.rglob("*.json")):
        payload = _try_load_json(path)
        if isinstance(payload, dict) and ("exploit" in payload or len(_SIDECAR_METADATA_KEYS.intersection(payload.keys())) >= 3):
            return payload, path
    return {}, None


def _try_load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _label_from_metadata(metadata: dict[str, Any]) -> int | None:
    if not metadata:
        return None
    raw_value = metadata.get("exploit")
    if isinstance(raw_value, bool):
        return int(raw_value)
    if isinstance(metadata.get("label"), bool):
        return int(metadata["label"])
    if isinstance(metadata.get("label"), int):
        return int(metadata["label"])
    if isinstance(metadata.get("is_malicious"), bool):
        return int(metadata["is_malicious"])
    if isinstance(metadata.get("is_attack"), bool):
        return int(metadata["is_attack"])
    return None


def _attack_stage_from_metadata(metadata: dict[str, Any], label: int | None) -> str | None:
    explicit_stage = metadata.get("attack_stage")
    if isinstance(explicit_stage, str) and explicit_stage.strip():
        return explicit_stage.strip()
    if label == 1:
        return "exfiltration"
    return None


def _infer_archive_source_type(paths: list[Path], archive_path: str | Path) -> SourceType | None:
    if any(path.suffix.lower() in _HOST_DATASET_EXTENSIONS for path in paths):
        return SourceType.HOST
    if any(path.suffix.lower() in _NETWORK_DATASET_EXTENSIONS for path in paths):
        return SourceType.NETWORK
    return _source_type_hint_from_path(archive_path)


def _infer_dataset_source_type(path: Path, preferred_source_type: SourceType | None, archive_path: str | Path) -> SourceType:
    suffix = path.suffix.lower()
    if suffix in _HOST_DATASET_EXTENSIONS:
        return SourceType.HOST
    if suffix in _NETWORK_DATASET_EXTENSIONS:
        return SourceType.NETWORK
    if preferred_source_type is not None:
        return preferred_source_type
    return _source_type_hint_from_path(archive_path) or SourceType.HOST


def _source_type_hint_from_path(path: str | Path) -> SourceType | None:
    text = str(path).lower()
    if "host" in text:
        return SourceType.HOST
    if any(token in text for token in ("dns", "network", "pcap", "flow")):
        return SourceType.NETWORK
    return None


def _select_feature_columns(frame: pd.DataFrame, *, max_features: int) -> list[str]:
    scored_columns: list[tuple[int, int, str]] = []
    for column in frame.columns:
        if column in CORE_EVENT_COLUMNS:
            continue
        series = frame[column]
        non_null = series.dropna()
        if non_null.empty:
            continue

        if pd.api.types.is_numeric_dtype(series):
            unique_count = int(non_null.nunique(dropna=True))
            score = int(non_null.shape[0]) + min(unique_count, 10) * 100
            scored_columns.append((score, unique_count, column))
            continue

        normalized_strings = non_null.astype(str)
        if column in _HIGH_CARDINALITY_COLUMNS:
            continue
        unique_count = int(normalized_strings.nunique(dropna=True))
        unique_ratio = unique_count / max(len(normalized_strings), 1)
        max_length = int(normalized_strings.str.len().max())
        if unique_count > 64 or unique_ratio > 0.8 or max_length > 96:
            continue
        score = int(non_null.shape[0]) + min(unique_count, 10) * 50
        scored_columns.append((score, unique_count, column))

    scored_columns.sort(key=lambda item: (-item[0], item[2]))
    return [column for _, _, column in scored_columns[:max_features]]


def _infer_feature_families(columns: list[str], source_type: SourceType) -> list[FeatureFamily]:
    families: set[FeatureFamily] = set()
    for column in columns:
        lowered = column.lower()
        if any(token in lowered for token in ("process", "syscall", "thread", "pid", "exec", "comm")):
            families.add(FeatureFamily.PROCESS)
        if any(token in lowered for token in ("file", "path", "storage", "fd", "dir", "mode", "dev")):
            families.add(FeatureFamily.FILE_SYSTEM)
        if any(token in lowered for token in ("uid", "gid", "euid", "privilege")):
            families.add(FeatureFamily.PRIVILEGE)
        if any(token in lowered for token in ("network", "socket", "proto", "port", "ip", "dns", "packet")):
            families.add(FeatureFamily.NETWORK_FLOW)
        if any(token in lowered for token in ("user", "session", "login")):
            families.add(FeatureFamily.USER_ACTIVITY)
        if any(token in lowered for token in ("sequence", "timestamp", "event_ts")):
            families.add(FeatureFamily.SEQUENCE)

    if not families:
        families.add(FeatureFamily.PROCESS if source_type == SourceType.HOST else FeatureFamily.NETWORK_FLOW)
    if source_type == SourceType.HOST and FeatureFamily.SEQUENCE not in families:
        families.add(FeatureFamily.SEQUENCE)
    return sorted(families, key=lambda item: item.value)
