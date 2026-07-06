"""Build final Stage Three model-ready artifacts."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from config import PATH_DATA_STORAGE
from scripts.db.models import FeatureArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.model_ready.registry import (
    ModelReadyArtifactRegistryService,
    RegisteredModelReadyArtifact,
)
from scripts.stage_three.model_ready.separator import FeatureSeparationResult, separate_feature_artifacts
from scripts.stage_three.model_ready.sequence_builder import (
    SequencePolicy,
    build_sequence_windows,
    sequence_windows_to_tables,
)
from scripts.stage_three.model_ready.split_index import (
    SplitIndexSummary,
    build_split_index_rows,
    validate_x_schema_consistency,
)
from scripts.stage_three.preprocessing.profiles import get_scaling_profile
from scripts.stage_two.model_ready.contracts import MODEL_READY_SCHEMA_VERSION


MODEL_READY_ROLES: tuple[str, ...] = ("TRAIN", "VALIDATION", "TEST")
TASK17_REPORT_FILENAME = "Task17-model-ready-builder.md"
TASK17_PREVIOUS_REPORT_PATH = "Task16-sequence-window-builder.md"
EXPERIMENT_ROLE = "EXPERIMENTS"


@dataclass(frozen=True)
class ModelReadyRoleBuildResult:
    """Model-ready output summary for one split role."""

    role: str
    source_feature_artifact_ids: list[int]
    artifacts: list[RegisteredModelReadyArtifact]
    x_row_count: int
    y_row_count: int
    feature_count: int
    target_distribution: dict[str, int]
    x_columns: list[str]
    sequence_artifact: RegisteredModelReadyArtifact | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly representation."""
        payload = asdict(self)
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        payload["sequence_artifact"] = (
            self.sequence_artifact.to_dict() if self.sequence_artifact is not None else None
        )
        return payload


@dataclass(frozen=True)
class ModelReadyBuildResult:
    """Final Task17 result for reports and CLI output."""

    status: str
    experiment_id: str
    branch: str
    preprocessing_profile: str
    target: str
    roles: list[str]
    role_results: list[ModelReadyRoleBuildResult]
    split_index_artifact: RegisteredModelReadyArtifact | None
    preprocessing_metadata_artifact: RegisteredModelReadyArtifact | None
    split_index_summary: SplitIndexSummary | None
    feature_count: int
    x_schema: list[str]
    warnings: list[str] = field(default_factory=list)
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly payload."""
        return {
            "status": self.status,
            "experiment_id": self.experiment_id,
            "branch": self.branch,
            "preprocessing_profile": self.preprocessing_profile,
            "target": self.target,
            "roles": list(self.roles),
            "role_results": [result.to_dict() for result in self.role_results],
            "split_index_artifact": (
                self.split_index_artifact.to_dict()
                if self.split_index_artifact is not None
                else None
            ),
            "preprocessing_metadata_artifact": (
                self.preprocessing_metadata_artifact.to_dict()
                if self.preprocessing_metadata_artifact is not None
                else None
            ),
            "split_index_summary": (
                asdict(self.split_index_summary)
                if self.split_index_summary is not None
                else None
            ),
            "feature_count": self.feature_count,
            "x_schema": list(self.x_schema),
            "warnings": list(self.warnings),
            "report_paths": dict(self.report_paths),
        }


def build_model_ready_artifacts(
    repository: ArtifactRepository,
    *,
    experiment_id: str,
    branch: str,
    preprocessing_profile: str,
    target: str,
    role: str | None = None,
    feature_group: str | None = None,
    storage_root: str | Path | None = None,
    resume: bool = False,
    include_sequences: bool = False,
    sequence_policy: SequencePolicy | None = None,
) -> ModelReadyBuildResult:
    """Build model-ready artifacts for one branch/profile and register catalog rows."""
    get_scaling_profile(preprocessing_profile)
    catalog = load_feature_catalog()
    registry = ModelReadyArtifactRegistryService(storage_root=storage_root or PATH_DATA_STORAGE)
    roles = [role] if role is not None else list(MODEL_READY_ROLES)
    role_results: list[ModelReadyRoleBuildResult] = []
    y_rows_by_role: dict[str, list[dict[str, Any]]] = {}
    x_columns_by_role: dict[str, list[str]] = {}
    warnings: list[str] = []

    for split_role in roles:
        feature_artifacts = repository.list_successful_feature_artifacts(
            branch=branch,
            role=split_role,
            feature_group=feature_group,
        )
        if not feature_artifacts:
            raise ValueError(
                f"no successful feature_artifacts found for branch={branch}, role={split_role}, "
                f"feature_group={feature_group or '*'}"
            )
        part_paths = _feature_part_paths(feature_artifacts, storage_root=storage_root or PATH_DATA_STORAGE)
        separation = separate_feature_artifacts(part_paths, feature_catalog=catalog)
        if target not in separation.y_columns:
            raise ValueError(f"target column {target!r} is missing from y columns for role={split_role}")
        source_feature_ids = [int(artifact.id) for artifact in feature_artifacts]
        first_feature_artifact_id = source_feature_ids[0] if source_feature_ids else None
        role_metadata = _role_metadata(
            experiment_id=experiment_id,
            branch=branch,
            preprocessing_profile=preprocessing_profile,
            target=target,
            feature_group=feature_group,
            role=split_role,
            source_feature_artifact_ids=source_feature_ids,
            part_paths=part_paths,
            separation=separation,
        )
        artifacts = [
            registry.register_rows(
                repository,
                separation.tables.X,
                experiment_id=experiment_id,
                branch=branch,
                preprocessing_profile=preprocessing_profile,
                role=split_role,
                data_type="X",
                file_name="X.parquet",
                feature_artifact_id=first_feature_artifact_id,
                feature_count=len(separation.x_columns),
                excluded_columns_json={"dropped_columns": [asdict(item) for item in separation.dropped_columns]},
                metadata_json=role_metadata,
                resume=resume,
            ),
            registry.register_rows(
                repository,
                _target_rows(separation.tables.y, target=target),
                experiment_id=experiment_id,
                branch=branch,
                preprocessing_profile=preprocessing_profile,
                role=split_role,
                data_type="y",
                file_name="y.parquet",
                feature_artifact_id=first_feature_artifact_id,
                label_distribution_json=_target_distribution(separation.tables.y, target),
                metadata_json=role_metadata,
                resume=resume,
            ),
            registry.register_rows(
                repository,
                separation.tables.metadata,
                experiment_id=experiment_id,
                branch=branch,
                preprocessing_profile=preprocessing_profile,
                role=split_role,
                data_type="metadata",
                file_name="metadata.parquet",
                feature_artifact_id=first_feature_artifact_id,
                metadata_json=role_metadata,
                resume=resume,
            ),
            registry.register_rows(
                repository,
                separation.tables.traceability,
                experiment_id=experiment_id,
                branch=branch,
                preprocessing_profile=preprocessing_profile,
                role=split_role,
                data_type="traceability",
                file_name="traceability.parquet",
                feature_artifact_id=first_feature_artifact_id,
                metadata_json=role_metadata,
                resume=resume,
            ),
        ]
        sequence_artifact = _build_sequence_artifact(
            repository,
            registry,
            part_paths=part_paths,
            experiment_id=experiment_id,
            branch=branch,
            preprocessing_profile=preprocessing_profile,
            role=split_role,
            source_feature_artifact_id=first_feature_artifact_id,
            include_sequences=include_sequences,
            sequence_policy=sequence_policy,
            resume=resume,
        )
        y_rows = _target_rows(separation.tables.y, target=target)
        y_rows_by_role[split_role] = y_rows
        x_columns_by_role[split_role] = list(separation.x_columns)
        role_results.append(
            ModelReadyRoleBuildResult(
                role=split_role,
                source_feature_artifact_ids=source_feature_ids,
                artifacts=artifacts,
                x_row_count=len(separation.tables.X),
                y_row_count=len(y_rows),
                feature_count=len(separation.x_columns),
                target_distribution=_target_distribution(separation.tables.y, target),
                x_columns=list(separation.x_columns),
                sequence_artifact=sequence_artifact,
            )
        )

    x_schema = validate_x_schema_consistency(x_columns_by_role)
    split_rows, split_summary = build_split_index_rows(
        y_rows_by_role,
        experiment_id=experiment_id,
        branch=branch,
        preprocessing_profile=preprocessing_profile,
    )
    split_index_artifact = registry.register_rows(
        repository,
        split_rows,
        experiment_id=experiment_id,
        branch=branch,
        preprocessing_profile=preprocessing_profile,
        role=EXPERIMENT_ROLE,
        data_type="split_index",
        file_name="split_index.parquet",
        feature_count=None,
        metadata_json={
            "experiment_id": experiment_id,
            "branch": branch,
            "preprocessing_profile": preprocessing_profile,
            "target": target,
            "roles": roles,
            "schema_version": MODEL_READY_SCHEMA_VERSION,
        },
        resume=resume,
    )
    preprocessing_metadata_artifact = registry.register_rows(
        repository,
        [_preprocessing_metadata_row(
            experiment_id=experiment_id,
            branch=branch,
            preprocessing_profile=preprocessing_profile,
            target=target,
            roles=roles,
            x_schema=x_schema,
            role_results=role_results,
            include_sequences=include_sequences,
        )],
        experiment_id=experiment_id,
        branch=branch,
        preprocessing_profile=preprocessing_profile,
        role=EXPERIMENT_ROLE,
        data_type="preprocessing_metadata",
        file_name="preprocessing_metadata.parquet",
        feature_count=len(x_schema),
        metadata_json={
            "experiment_id": experiment_id,
            "branch": branch,
            "preprocessing_profile": preprocessing_profile,
            "target": target,
            "fitted_on_role": "TRAIN",
        },
        resume=resume,
    )
    feature_counts = {result.feature_count for result in role_results}
    if len(feature_counts) > 1:
        warnings.append("feature_count differs across roles even though schema validation passed")
    return ModelReadyBuildResult(
        status="SUCCESS",
        experiment_id=experiment_id,
        branch=branch,
        preprocessing_profile=preprocessing_profile,
        target=target,
        roles=roles,
        role_results=role_results,
        split_index_artifact=split_index_artifact,
        preprocessing_metadata_artifact=preprocessing_metadata_artifact,
        split_index_summary=split_summary,
        feature_count=len(x_schema),
        x_schema=x_schema,
        warnings=warnings,
    )


def _feature_part_paths(
    artifacts: list[FeatureArtifact],
    *,
    storage_root: str | Path,
) -> list[Path]:
    paths: list[Path] = []
    for artifact in artifacts:
        metadata = artifact.metadata_json or {}
        parts = metadata.get("parts")
        added_for_artifact = False
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("path"), str):
                    paths.append(_resolve_storage_path(part["path"], storage_root=storage_root))
                    added_for_artifact = True
        if added_for_artifact:
            continue
        feature_path = _resolve_storage_path(artifact.feature_path, storage_root=storage_root)
        if feature_path.is_file():
            paths.append(feature_path)
        elif feature_path.is_dir():
            paths.extend(sorted(feature_path.glob("*.parquet")))
    existing = [path for path in paths if path.exists()]
    if not existing:
        raise ValueError("feature_artifacts do not reference existing Parquet parts")
    return existing


def _resolve_storage_path(path: str, *, storage_root: str | Path) -> Path:
    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved
    return Path(storage_root).expanduser() / resolved


def _role_metadata(
    *,
    experiment_id: str,
    branch: str,
    preprocessing_profile: str,
    target: str,
    feature_group: str | None,
    role: str,
    source_feature_artifact_ids: list[int],
    part_paths: list[Path],
    separation: FeatureSeparationResult,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "branch": branch,
        "role": role,
        "preprocessing_profile": preprocessing_profile,
        "target": target,
        "feature_group": feature_group,
        "source_feature_artifact_ids": source_feature_artifact_ids,
        "source_feature_part_paths": [path.as_posix() for path in part_paths],
        "source_columns": separation.source_columns,
        "x_columns": separation.x_columns,
        "y_columns": separation.y_columns,
        "metadata_columns": separation.metadata_columns,
        "traceability_columns": separation.traceability_columns,
        "dropped_columns": [asdict(item) for item in separation.dropped_columns],
        "schema_version": MODEL_READY_SCHEMA_VERSION,
    }


def _target_rows(rows: list[dict[str, Any]], *, target: str) -> list[dict[str, Any]]:
    return [
        {
            "sample_uid": row.get("sample_uid"),
            target: row.get(target),
            **{
                column: value
                for column, value in row.items()
                if column not in {"sample_uid", target}
            },
        }
        for row in rows
    ]


def _target_distribution(rows: list[dict[str, Any]], target: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(target)
        counter["unlabeled" if value is None else str(value)] += 1
    return dict(sorted(counter.items()))


def _build_sequence_artifact(
    repository: ArtifactRepository,
    registry: ModelReadyArtifactRegistryService,
    *,
    part_paths: list[Path],
    experiment_id: str,
    branch: str,
    preprocessing_profile: str,
    role: str,
    source_feature_artifact_id: int | None,
    include_sequences: bool,
    sequence_policy: SequencePolicy | None,
    resume: bool,
) -> RegisteredModelReadyArtifact | None:
    if not include_sequences:
        return None
    rows = [
        row
        for path in part_paths
        for row in pq.read_table(path).to_pylist()
    ]
    result = build_sequence_windows(
        rows,
        branch=branch,
        role=role,
        policy=sequence_policy,
    )
    sequence_rows = sequence_windows_to_tables(result)["X"]
    return registry.register_rows(
        repository,
        sequence_rows,
        experiment_id=experiment_id,
        branch=branch,
        preprocessing_profile=preprocessing_profile,
        role=role,
        data_type="sequence",
        file_name="sequence.parquet",
        feature_artifact_id=source_feature_artifact_id,
        feature_count=None,
        sequence_length=result.policy.sequence_length,
        metadata_json={
            "experiment_id": experiment_id,
            "branch": branch,
            "role": role,
            "preprocessing_profile": preprocessing_profile,
            "sequence_policy": result.policy.to_dict(),
            "label_distribution": result.label_distribution,
            "padding_statistics": result.padding_statistics,
            "ordering_policy": result.ordering_policy,
        },
        resume=resume,
    )


def _preprocessing_metadata_row(
    *,
    experiment_id: str,
    branch: str,
    preprocessing_profile: str,
    target: str,
    roles: list[str],
    x_schema: list[str],
    role_results: list[ModelReadyRoleBuildResult],
    include_sequences: bool,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "branch": branch,
        "preprocessing_profile": preprocessing_profile,
        "target": target,
        "fitted_on_role": "TRAIN",
        "roles_json": json.dumps(roles, ensure_ascii=False),
        "x_schema_json": json.dumps(x_schema, ensure_ascii=False),
        "feature_count": len(x_schema),
        "sequence_profile_enabled": include_sequences,
        "role_artifact_ids_json": json.dumps(
            {
                result.role: [artifact.catalog_id for artifact in result.artifacts]
                for result in role_results
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def with_report_paths(
    result: ModelReadyBuildResult,
    report_paths: dict[str, str],
) -> ModelReadyBuildResult:
    """Return a result enriched with written report paths."""
    return replace(result, report_paths=report_paths)
