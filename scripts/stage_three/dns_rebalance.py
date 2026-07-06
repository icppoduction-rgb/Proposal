"""DNS supervised 70/30 split rebuild with source exclusions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import (
    BACKUPS_POSTGRES_CATALOG_RELATIVE,
    PATH_DATA_STORAGE,
    REPORTS_RU_STAGE_THREE,
)
from scripts.db.models import DatasetFile, FeatureArtifact, ModelReadyArtifact, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_two.model_ready.contracts import MODEL_READY_SCHEMA_VERSION


POLICY_ID = "dns_supervised_70_30_v1"
BRANCH = "dns"
FEATURE_GROUP = "dns_lexical"
PREPROCESSING_PROFILE = "tree_unscaled"
TARGET = "label_binary"
SOURCE_ATTACK_LIMIT_REQUESTED = 3_680_106

TARGET_COUNTS: dict[str, dict[int, int]] = {
    "TRAIN": {0: 6_010_841, 1: 2_576_074},
    "VALIDATION": {0: 1_288_037, 1: 552_016},
    "TEST": {0: 1_288_037, 1: 552_016},
}

X_COLUMNS: tuple[str, ...] = (
    "dns_query_length",
    "dns_subdomain_length",
    "dns_label_count",
    "dns_label_avg_len",
    "dns_label_max_len",
    "dns_digit_count",
    "dns_special_char_count",
)

FULLY_EXCLUDED_ATTACK_FILE = (
    r"C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap"
    r"\ens33-dns_amplification_attack.pcap"
)
LIMITED_ATTACK_FILE = (
    r"C:\Users\Public\PythonProjects\storages\datasets-filter\dns\VALIDATION\pcap"
    r"\ens33-dns_amplification_attack__f291ed87a1.pcap"
)


@dataclass(frozen=True)
class DnsRebalanceRequest:
    """Operational request for DNS supervised split rebuild."""

    experiment_id: str = "dns_rebalanced_70_30_v1"
    feature_group: str = FEATURE_GROUP
    preprocessing_profile: str = PREPROCESSING_PROFILE
    target: str = TARGET
    storage_root: str | Path = PATH_DATA_STORAGE
    dry_run: bool = True
    overwrite: bool = False
    apply_catalog: bool = False
    deactivate_existing_experiment: str | None = None


@dataclass(frozen=True)
class DnsCatalogImpact:
    """Catalog rows affected by the exclusion policy."""

    fully_excluded_file_ids: list[int]
    limited_attack_file_ids: list[int]
    test_csv_file_ids: list[int]
    normalized_artifact_ids_to_skip: list[int]
    feature_artifact_ids_to_skip: list[int]
    model_ready_artifact_ids_to_skip: list[int]
    existing_experiment_artifact_ids_to_skip: list[int]


@dataclass(frozen=True)
class DnsRebalanceResult:
    """Serializable DNS rebalance result."""

    status: str
    policy_id: str
    experiment_id: str
    dry_run: bool
    apply_catalog: bool
    target_counts: dict[str, dict[str, int]]
    current_counts: list[dict[str, Any]]
    selected_counts: list[dict[str, Any]]
    exclusion_counts: dict[str, Any]
    duplicate_checks: dict[str, int]
    output_artifacts: list[dict[str, Any]] = field(default_factory=list)
    catalog_impact: dict[str, Any] = field(default_factory=dict)
    catalog_updates: dict[str, int] = field(default_factory=dict)
    report_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly result."""
        return asdict(self)


def run_dns_supervised_rebalance(
    session: Session,
    request: DnsRebalanceRequest,
) -> DnsRebalanceResult:
    """Audit or build the DNS 70/30 supervised split artifacts."""
    if request.feature_group != FEATURE_GROUP:
        raise ValueError("DNS supervised rebalance currently supports only feature_group=dns_lexical")
    if request.target != TARGET:
        raise ValueError("DNS supervised rebalance currently supports only target=label_binary")
    storage_root = Path(request.storage_root).expanduser()
    if not storage_root.exists():
        raise ValueError(f"storage_root does not exist: {storage_root}")

    impact = collect_catalog_impact(session, deactivate_existing_experiment=request.deactivate_existing_experiment)
    con = _connect_duckdb(storage_root)
    try:
        _create_id_table(con, "excluded_normalized_ids", impact.normalized_artifact_ids_to_skip)
        _create_id_table(con, "limited_attack_normalized_ids", _normalized_ids_for_files(session, impact.limited_attack_file_ids))
        _create_candidate_tables(con, storage_root=storage_root, feature_group=request.feature_group)
        current_counts = _fetch_dicts(
            con,
            "SELECT source_role AS role, label_binary, rows FROM dns_source_counts ORDER BY source_role, label_binary",
        )
        _create_selected_split(con)
        selected_counts = _fetch_dicts(
            con,
            """
            SELECT target_role AS role, CAST(label_binary_int AS VARCHAR) AS label_binary, COUNT(*) AS rows
            FROM dns_selected_split
            GROUP BY target_role, label_binary
            ORDER BY target_role, label_binary
            """,
        )
        exclusion_counts = _exclusion_counts(con)
        duplicate_checks = _duplicate_checks(con)
        warnings = _build_warnings(selected_counts, exclusion_counts, duplicate_checks)
        output_artifacts: list[dict[str, Any]] = []
        catalog_updates: dict[str, int] = {}
        if not request.dry_run:
            output_artifacts = _write_model_ready_artifacts(
                con,
                storage_root=storage_root,
                request=request,
            )
            if request.apply_catalog:
                backup_path = _backup_catalog_rows(session, storage_root=storage_root, impact=impact)
                catalog_updates = _apply_catalog_updates(
                    session,
                    storage_root=storage_root,
                    request=request,
                    impact=impact,
                    output_artifacts=output_artifacts,
                    backup_path=backup_path,
                )
    finally:
        con.close()

    status = "SUCCESS" if not warnings else "PARTIAL_SUCCESS"
    result = DnsRebalanceResult(
        status=status,
        policy_id=POLICY_ID,
        experiment_id=request.experiment_id,
        dry_run=request.dry_run,
        apply_catalog=request.apply_catalog,
        target_counts=_string_key_target_counts(),
        current_counts=current_counts,
        selected_counts=selected_counts,
        exclusion_counts=exclusion_counts,
        duplicate_checks=duplicate_checks,
        output_artifacts=output_artifacts,
        catalog_impact=asdict(impact),
        catalog_updates=catalog_updates,
        warnings=warnings,
    )
    return save_dns_rebalance_report(result, storage_root=storage_root)


def collect_catalog_impact(
    session: Session,
    *,
    deactivate_existing_experiment: str | None,
) -> DnsCatalogImpact:
    """Collect catalog ids affected by raw source exclusions."""
    fully_excluded_file_ids = _dataset_file_ids_for_path(session, FULLY_EXCLUDED_ATTACK_FILE)
    limited_attack_file_ids = _dataset_file_ids_for_path(session, LIMITED_ATTACK_FILE)
    test_csv_file_ids = [
        int(file_id)
        for file_id in session.execute(
            select(DatasetFile.id).where(
                DatasetFile.branch == BRANCH,
                DatasetFile.role == "TEST",
                DatasetFile.source_format == "csv",
            )
        ).scalars()
    ]
    files_to_skip = sorted(set(fully_excluded_file_ids + test_csv_file_ids))
    normalized_artifact_ids_to_skip = _normalized_ids_for_files(session, files_to_skip)
    feature_artifact_ids_to_skip = [
        int(artifact_id)
        for artifact_id in session.execute(
            select(FeatureArtifact.id).where(
                FeatureArtifact.normalized_artifact_id.in_(normalized_artifact_ids_to_skip)
            )
        ).scalars()
    ] if normalized_artifact_ids_to_skip else []
    model_ready_artifact_ids_to_skip = [
        int(artifact_id)
        for artifact_id in session.execute(
            select(ModelReadyArtifact.id).where(
                ModelReadyArtifact.feature_artifact_id.in_(feature_artifact_ids_to_skip)
            )
        ).scalars()
    ] if feature_artifact_ids_to_skip else []
    existing_experiment_artifact_ids_to_skip: list[int] = []
    if deactivate_existing_experiment:
        existing_experiment_artifact_ids_to_skip = [
            int(artifact.id)
            for artifact in session.execute(
                select(ModelReadyArtifact).where(
                    ModelReadyArtifact.branch == BRANCH,
                    ModelReadyArtifact.status == "SUCCESS",
                )
            ).scalars()
            if (artifact.metadata_json or {}).get("experiment_id") == deactivate_existing_experiment
        ]
    return DnsCatalogImpact(
        fully_excluded_file_ids=sorted(set(fully_excluded_file_ids)),
        limited_attack_file_ids=sorted(set(limited_attack_file_ids)),
        test_csv_file_ids=sorted(set(test_csv_file_ids)),
        normalized_artifact_ids_to_skip=sorted(set(normalized_artifact_ids_to_skip)),
        feature_artifact_ids_to_skip=sorted(set(feature_artifact_ids_to_skip)),
        model_ready_artifact_ids_to_skip=sorted(set(model_ready_artifact_ids_to_skip)),
        existing_experiment_artifact_ids_to_skip=sorted(set(existing_experiment_artifact_ids_to_skip)),
    )


def save_dns_rebalance_report(
    result: DnsRebalanceResult,
    *,
    storage_root: str | Path,
) -> DnsRebalanceResult:
    """Write JSON and Markdown audit reports."""
    root = Path(storage_root).expanduser()
    report_dir = _report_dir(root)
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{result.experiment_id}_dns_rebalanced_split_report"
    json_path = report_dir / f"{stem}.json"
    md_path = report_dir / f"{stem}.md"
    payload = result.to_dict()
    payload["report_paths"] = {}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown_report(payload), encoding="utf-8")
    report_paths = {
        "json": _relative_or_absolute(json_path, root),
        "markdown": _relative_or_absolute(md_path, root),
    }
    return DnsRebalanceResult(**{**payload, "report_paths": report_paths})


def _connect_duckdb(storage_root: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.execute("SET memory_limit='20GB'")
    con.execute("SET threads=3")
    con.execute("SET preserve_insertion_order=false")
    temp_dir = storage_root / "temp_data" / "duckdb"
    temp_dir.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory='{_sql_string(temp_dir.as_posix())}'")
    con.execute("SET max_temp_directory_size='100GB'")
    return con


def _create_candidate_tables(
    con: duckdb.DuckDBPyConnection,
    *,
    storage_root: Path,
    feature_group: str,
) -> None:
    features_glob = (storage_root / "parquet" / "features" / feature_group / BRANCH / "*" / "schema=v1" / "*.parquet").as_posix()
    con.execute(
        f"""
        CREATE TEMP TABLE dns_source_counts AS
        SELECT role AS source_role,
               CASE
                   WHEN TRY_CAST(label_binary AS INTEGER) IS NULL THEN 'NULL'
                   ELSE CAST(TRY_CAST(label_binary AS INTEGER) AS VARCHAR)
               END AS label_binary,
               COUNT(*) AS rows
        FROM read_parquet('{_sql_string(features_glob)}', union_by_name=true, filename=true)
        WHERE branch = '{BRANCH}'
          AND feature_group = '{_sql_string(feature_group)}'
        GROUP BY source_role, label_binary
        """
    )
    con.execute(
        f"""
        CREATE TEMP TABLE dns_candidates AS
        SELECT
            sample_uid,
            normalized_artifact_id,
            source_event_uid_refs,
            source_normalized_path,
            dataset_id,
            role AS source_role,
            branch,
            feature_group,
            {", ".join(X_COLUMNS)},
            TRY_CAST(label_binary AS INTEGER) AS label_binary_int,
            label_family,
            label_subtype,
            label_source,
            label_status,
            label_confidence,
            label_mapping_rule_id,
            md5(
                COALESCE(CAST(sample_uid AS VARCHAR), '') || '|' ||
                COALESCE(CAST(normalized_artifact_id AS VARCHAR), '') || '|' ||
                COALESCE(CAST(source_event_uid_refs AS VARCHAR), '')
            ) AS event_key
        FROM read_parquet('{_sql_string(features_glob)}', union_by_name=true, filename=true)
        WHERE branch = '{BRANCH}'
          AND feature_group = '{_sql_string(feature_group)}'
          AND role <> 'TEST'
          AND TRY_CAST(label_binary AS INTEGER) IN (0, 1)
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE dns_eligible AS
        SELECT c.*
        FROM dns_candidates c
        LEFT JOIN excluded_normalized_ids e
            ON c.normalized_artifact_id = e.id
        WHERE e.id IS NULL
          AND c.source_role <> 'TEST'
          AND c.label_binary_int IN (0, 1)
        """
    )


def _create_selected_split(con: duckdb.DuckDBPyConnection) -> None:
    normal_target = _target_total_for_label(0)
    attack_target = _target_total_for_label(1)
    con.execute(
        f"""
        CREATE TEMP TABLE dns_selected_pool AS
        SELECT *
        FROM (
            SELECT *
            FROM dns_eligible
            WHERE label_binary_int = 0
            ORDER BY event_key
            LIMIT {normal_target}
        )
        UNION ALL
        SELECT *
        FROM (
            SELECT *
            FROM dns_eligible
            WHERE label_binary_int = 1
            ORDER BY CASE WHEN source_role = 'TRAIN' THEN 0 ELSE 1 END, event_key
            LIMIT {attack_target}
        )
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE dns_selected_ranked AS
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY label_binary_int
                   ORDER BY
                       CASE WHEN label_binary_int = 1 AND source_role = 'TRAIN' THEN 0 ELSE 1 END,
                       event_key
               ) AS split_rank
        FROM dns_selected_pool
        """
    )
    train_normal = TARGET_COUNTS["TRAIN"][0]
    validation_normal_end = train_normal + TARGET_COUNTS["VALIDATION"][0]
    train_attack = TARGET_COUNTS["TRAIN"][1]
    validation_attack_end = train_attack + TARGET_COUNTS["VALIDATION"][1]
    con.execute(
        f"""
        CREATE TEMP TABLE dns_selected_split AS
        SELECT *,
               CASE
                   WHEN label_binary_int = 0 AND split_rank <= {train_normal} THEN 'TRAIN'
                   WHEN label_binary_int = 0 AND split_rank <= {validation_normal_end} THEN 'VALIDATION'
                   WHEN label_binary_int = 0 THEN 'TEST'
                   WHEN label_binary_int = 1 AND split_rank <= {train_attack} THEN 'TRAIN'
                   WHEN label_binary_int = 1 AND split_rank <= {validation_attack_end} THEN 'VALIDATION'
                   ELSE 'TEST'
               END AS target_role,
               split_rank - 1 AS target_row_index
        FROM dns_selected_ranked
        """
    )


def _write_model_ready_artifacts(
    con: duckdb.DuckDBPyConnection,
    *,
    storage_root: Path,
    request: DnsRebalanceRequest,
) -> list[dict[str, Any]]:
    output_root = (
        storage_root
        / "parquet"
        / "model_ready"
        / request.experiment_id
        / BRANCH
        / request.preprocessing_profile
    )
    artifacts: list[dict[str, Any]] = []
    for role in ("TRAIN", "VALIDATION", "TEST"):
        role_dir = output_root / role
        role_dir.mkdir(parents=True, exist_ok=True)
        artifacts.extend(
            [
                _copy_artifact(
                    con,
                    storage_root=storage_root,
                    path=role_dir / "X.parquet",
                    data_type="X",
                    role=role,
                    request=request,
                    sql=f"""
                        SELECT {", ".join(X_COLUMNS)}
                        FROM dns_selected_split
                        WHERE target_role = '{role}'
                        ORDER BY label_binary_int, split_rank
                    """,
                ),
                _copy_artifact(
                    con,
                    storage_root=storage_root,
                    path=role_dir / "y.parquet",
                    data_type="y",
                    role=role,
                    request=request,
                    sql=f"""
                        SELECT sample_uid, label_binary_int AS label_binary
                        FROM dns_selected_split
                        WHERE target_role = '{role}'
                        ORDER BY label_binary_int, split_rank
                    """,
                ),
                _copy_artifact(
                    con,
                    storage_root=storage_root,
                    path=role_dir / "metadata.parquet",
                    data_type="metadata",
                    role=role,
                    request=request,
                    sql=f"""
                        SELECT sample_uid,
                               source_role,
                               branch,
                               feature_group,
                               label_status,
                               label_source,
                               label_confidence,
                               label_mapping_rule_id
                        FROM dns_selected_split
                        WHERE target_role = '{role}'
                        ORDER BY label_binary_int, split_rank
                    """,
                ),
                _copy_artifact(
                    con,
                    storage_root=storage_root,
                    path=role_dir / "traceability.parquet",
                    data_type="traceability",
                    role=role,
                    request=request,
                    sql=f"""
                        SELECT sample_uid,
                               event_key,
                               normalized_artifact_id,
                               source_normalized_path,
                               dataset_id,
                               source_role,
                               target_role,
                               label_binary_int AS label_binary,
                               '{POLICY_ID}' AS split_policy_id
                        FROM dns_selected_split
                        WHERE target_role = '{role}'
                        ORDER BY label_binary_int, split_rank
                    """,
                ),
            ]
        )
    experiment_dir = output_root / "EXPERIMENTS"
    experiment_dir.mkdir(parents=True, exist_ok=True)
    artifacts.append(
        _copy_artifact(
            con,
            storage_root=storage_root,
            path=experiment_dir / "split_index.parquet",
            data_type="split_index",
            role="EXPERIMENTS",
            request=request,
            sql=f"""
                SELECT '{request.experiment_id}' AS experiment_id,
                       '{BRANCH}' AS branch,
                       '{request.preprocessing_profile}' AS preprocessing_profile,
                       target_role AS role,
                       sample_uid,
                       ROW_NUMBER() OVER (PARTITION BY target_role ORDER BY label_binary_int, split_rank) - 1 AS row_index
                FROM dns_selected_split
                ORDER BY role, row_index
            """,
        )
    )
    preprocessing_path = experiment_dir / "preprocessing_metadata.parquet"
    _ensure_can_write(preprocessing_path, overwrite=request.overwrite)
    con.execute(
        f"""
        COPY (
            SELECT '{request.experiment_id}' AS experiment_id,
                   '{BRANCH}' AS branch,
                   '{request.preprocessing_profile}' AS preprocessing_profile,
                   '{TARGET}' AS target,
                   'TRAIN' AS fitted_on_role,
                   '{json.dumps(["TRAIN", "VALIDATION", "TEST"])}' AS roles_json,
                   '{json.dumps(list(X_COLUMNS))}' AS x_schema_json,
                   {len(X_COLUMNS)} AS feature_count,
                   false AS sequence_profile_enabled,
                   '{POLICY_ID}' AS split_policy_id,
                   '{datetime.now(timezone.utc).isoformat()}' AS created_at
        ) TO '{_sql_string(preprocessing_path.as_posix())}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    artifacts.append(_artifact_payload(preprocessing_path, storage_root, "EXPERIMENTS", "preprocessing_metadata", 1, len(X_COLUMNS)))
    return artifacts


def _copy_artifact(
    con: duckdb.DuckDBPyConnection,
    *,
    storage_root: Path,
    path: Path,
    data_type: str,
    role: str,
    request: DnsRebalanceRequest,
    sql: str,
) -> dict[str, Any]:
    _ensure_can_write(path, overwrite=request.overwrite)
    con.execute(f"COPY ({sql}) TO '{_sql_string(path.as_posix())}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    row_count = int(con.execute(f"SELECT COUNT(*) FROM read_parquet('{_sql_string(path.as_posix())}')").fetchone()[0])
    feature_count = len(X_COLUMNS) if data_type in {"X", "preprocessing_metadata"} else None
    return _artifact_payload(path, storage_root, role, data_type, row_count, feature_count)


def _artifact_payload(
    path: Path,
    storage_root: Path,
    role: str,
    data_type: str,
    row_count: int,
    feature_count: int | None,
) -> dict[str, Any]:
    return {
        "role": role,
        "data_type": data_type,
        "artifact_path": _relative_or_absolute(path, storage_root),
        "sample_count": row_count,
        "feature_count": feature_count,
    }


def _apply_catalog_updates(
    session: Session,
    *,
    storage_root: Path,
    request: DnsRebalanceRequest,
    impact: DnsCatalogImpact,
    output_artifacts: list[dict[str, Any]],
    backup_path: Path,
) -> dict[str, int]:
    policy_metadata = {
        "policy_id": POLICY_ID,
        "reason": "DNS supervised 70/30 split rebuild",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "backup_path": _relative_or_absolute(backup_path, storage_root),
    }
    updates: dict[str, int] = {}
    raw_ids_to_skip = sorted(set(impact.fully_excluded_file_ids + impact.test_csv_file_ids))
    updates["dataset_files_skipped"] = _mark_dataset_files_skipped(session, raw_ids_to_skip, policy_metadata)
    updates["normalized_artifacts_skipped"] = _mark_artifacts_skipped(
        session,
        NormalizedArtifact,
        impact.normalized_artifact_ids_to_skip,
        policy_metadata,
    )
    updates["feature_artifacts_skipped"] = _mark_artifacts_skipped(
        session,
        FeatureArtifact,
        impact.feature_artifact_ids_to_skip,
        policy_metadata,
    )
    model_ready_to_skip = sorted(
        set(impact.model_ready_artifact_ids_to_skip + impact.existing_experiment_artifact_ids_to_skip)
    )
    updates["model_ready_artifacts_skipped"] = _mark_artifacts_skipped(
        session,
        ModelReadyArtifact,
        model_ready_to_skip,
        policy_metadata,
    )
    repository = ArtifactRepository(session)
    representative_feature_ids = _representative_feature_ids_by_role(session)
    source_feature_ids = _source_feature_ids_by_role(session)
    registered = 0
    for artifact in output_artifacts:
        label_distribution = _target_distribution_for_role(artifact["role"]) if artifact["data_type"] == "y" else None
        feature_artifact_id = representative_feature_ids.get(artifact["role"]) or representative_feature_ids.get("TRAIN")
        repository.register_model_ready_artifact(
            artifact_uid=uuid4(),
            feature_artifact_id=feature_artifact_id,
            preprocessing_artifact_id=None,
            role=artifact["role"],
            branch=BRANCH,
            data_type=artifact["data_type"],
            artifact_path=artifact["artifact_path"],
            schema_name="model_ready",
            schema_version=MODEL_READY_SCHEMA_VERSION,
            sample_count=artifact["sample_count"],
            feature_count=artifact["feature_count"],
            label_distribution_json=label_distribution,
            excluded_columns_json={"x_forbidden_columns_excluded": True} if artifact["data_type"] == "X" else None,
            sequence_length=None,
            status="SUCCESS",
            metadata_json={
                "experiment_id": request.experiment_id,
                "policy_id": POLICY_ID,
                "preprocessing_profile": request.preprocessing_profile,
                "fitted_on_role": "TRAIN",
                "target": request.target,
                "source_feature_group": request.feature_group,
                "source_feature_artifact_ids_by_role": source_feature_ids,
                "representative_feature_artifact_id": feature_artifact_id,
            },
        )
        registered += 1
    updates["model_ready_artifacts_registered"] = registered
    session.flush()
    return updates


def _representative_feature_ids_by_role(session: Session) -> dict[str, int]:
    rows = list(
        session.execute(
            select(FeatureArtifact)
            .where(
                FeatureArtifact.branch == BRANCH,
                FeatureArtifact.feature_group == FEATURE_GROUP,
                FeatureArtifact.status == "SUCCESS",
            )
            .order_by(FeatureArtifact.role.asc(), FeatureArtifact.id.asc())
        ).scalars()
    )
    by_role: dict[str, int] = {}
    for row in rows:
        by_role.setdefault(row.role, int(row.id))
    if "TEST" not in by_role and "TRAIN" in by_role:
        by_role["TEST"] = by_role["TRAIN"]
    if "EXPERIMENTS" not in by_role and "TRAIN" in by_role:
        by_role["EXPERIMENTS"] = by_role["TRAIN"]
    return by_role


def _source_feature_ids_by_role(session: Session) -> dict[str, list[int]]:
    rows = list(
        session.execute(
            select(FeatureArtifact.id, FeatureArtifact.role)
            .where(
                FeatureArtifact.branch == BRANCH,
                FeatureArtifact.feature_group == FEATURE_GROUP,
                FeatureArtifact.status == "SUCCESS",
            )
            .order_by(FeatureArtifact.role.asc(), FeatureArtifact.id.asc())
        ).all()
    )
    payload: dict[str, list[int]] = {}
    for artifact_id, role in rows:
        payload.setdefault(str(role), []).append(int(artifact_id))
    return payload


def _backup_catalog_rows(session: Session, *, storage_root: Path, impact: DnsCatalogImpact) -> Path:
    backup_dir = storage_root / BACKUPS_POSTGRES_CATALOG_RELATIVE
    backup_dir.mkdir(parents=True, exist_ok=True)
    path = backup_dir / f"{POLICY_ID}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    payload = {
        "policy_id": POLICY_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "impact": asdict(impact),
        "dataset_files": _model_rows(session, DatasetFile, impact.fully_excluded_file_ids + impact.test_csv_file_ids),
        "normalized_artifacts": _model_rows(session, NormalizedArtifact, impact.normalized_artifact_ids_to_skip),
        "feature_artifacts": _model_rows(session, FeatureArtifact, impact.feature_artifact_ids_to_skip),
        "model_ready_artifacts": _model_rows(
            session,
            ModelReadyArtifact,
            impact.model_ready_artifact_ids_to_skip + impact.existing_experiment_artifact_ids_to_skip,
        ),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path


def _model_rows(session: Session, model: type[Any], ids: list[int]) -> list[dict[str, Any]]:
    if not ids:
        return []
    rows = list(session.execute(select(model).where(model.id.in_(sorted(set(ids))))).scalars())
    return [
        {column.name: getattr(row, column.name) for column in row.__table__.columns}
        for row in rows
    ]


def _mark_dataset_files_skipped(
    session: Session,
    ids: list[int],
    metadata: dict[str, Any],
) -> int:
    if not ids:
        return 0
    rows = list(session.execute(select(DatasetFile).where(DatasetFile.id.in_(ids))).scalars())
    for row in rows:
        row.status = "SKIPPED"
        row.error_message = f"{POLICY_ID}: excluded from DNS supervised training/evaluation"
        row.metadata_json = _append_policy_metadata(row.metadata_json, metadata)
    session.flush()
    return len(rows)


def _mark_artifacts_skipped(
    session: Session,
    model: type[Any],
    ids: list[int],
    metadata: dict[str, Any],
) -> int:
    if not ids:
        return 0
    rows = list(session.execute(select(model).where(model.id.in_(ids))).scalars())
    for row in rows:
        row.status = "SKIPPED"
        row.metadata_json = _append_policy_metadata(row.metadata_json, metadata)
    session.flush()
    return len(rows)


def _append_policy_metadata(existing: dict[str, Any] | None, metadata: dict[str, Any]) -> dict[str, Any]:
    payload = dict(existing or {})
    policies = payload.get("exclusion_policies")
    if not isinstance(policies, list):
        policies = []
    policies.append(dict(metadata))
    payload["exclusion_policies"] = policies
    payload["not_for_training"] = True
    return payload


def _exclusion_counts(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    rows = _fetch_dicts(con, "SELECT * FROM dns_source_counts ORDER BY source_role, label_binary")
    selected_total = int(con.execute("SELECT COUNT(*) FROM dns_selected_split").fetchone()[0])
    selected_attack_from_limited_source = int(
        con.execute(
            """
            SELECT COUNT(*)
            FROM dns_selected_split s
            JOIN limited_attack_normalized_ids ids
                ON s.normalized_artifact_id = ids.id
            WHERE s.label_binary_int = 1
            """
        ).fetchone()[0]
    )
    available_attack_from_limited_source = int(
        con.execute(
            """
            SELECT COUNT(*)
            FROM dns_eligible s
            JOIN limited_attack_normalized_ids ids
                ON s.normalized_artifact_id = ids.id
            WHERE s.label_binary_int = 1
            """
        ).fetchone()[0]
    )
    return {
        "source_counts_before_selection": rows,
        "selected_total": selected_total,
        "bad_test_csv_rows_excluded": int(
            con.execute("SELECT COALESCE(SUM(rows), 0) FROM dns_source_counts WHERE source_role = 'TEST'").fetchone()[0]
        ),
        "null_label_rows_excluded": int(
            con.execute("SELECT COALESCE(SUM(rows), 0) FROM dns_source_counts WHERE label_binary = 'NULL'").fetchone()[0]
        ),
        "fully_excluded_attack_file_rows": int(
            con.execute(
                """
                SELECT COUNT(*)
                FROM dns_candidates c
                JOIN excluded_normalized_ids e ON c.normalized_artifact_id = e.id
                WHERE c.source_role = 'VALIDATION'
                """
            ).fetchone()[0]
        ),
        "available_attack_from_limited_source": available_attack_from_limited_source,
        "selected_attack_from_limited_source": selected_attack_from_limited_source,
        "requested_attack_source_limit": SOURCE_ATTACK_LIMIT_REQUESTED,
        "effective_attack_source_selection": selected_attack_from_limited_source,
        "limited_source_rows_excluded_by_global_target": max(
            available_attack_from_limited_source - selected_attack_from_limited_source,
            0,
        ),
    }


def _duplicate_checks(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {
        "selected_duplicate_event_key_rows": int(
            con.execute(
                "SELECT COUNT(*) - COUNT(DISTINCT event_key) FROM dns_selected_split"
            ).fetchone()[0]
        ),
        "selected_duplicate_sample_uid_rows": int(
            con.execute(
                "SELECT COUNT(*) - COUNT(DISTINCT sample_uid) FROM dns_selected_split"
            ).fetchone()[0]
        ),
        "event_keys_in_multiple_target_roles": int(
            con.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT event_key
                    FROM dns_selected_split
                    GROUP BY event_key
                    HAVING COUNT(DISTINCT target_role) > 1
                )
                """
            ).fetchone()[0]
        ),
        "sample_uids_in_multiple_target_roles": int(
            con.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT sample_uid
                    FROM dns_selected_split
                    GROUP BY sample_uid
                    HAVING COUNT(DISTINCT target_role) > 1
                )
                """
            ).fetchone()[0]
        ),
        "selected_null_label_rows": int(
            con.execute("SELECT COUNT(*) FROM dns_selected_split WHERE label_binary_int IS NULL").fetchone()[0]
        ),
        "selected_bad_test_source_rows": int(
            con.execute("SELECT COUNT(*) FROM dns_selected_split WHERE source_role = 'TEST'").fetchone()[0]
        ),
    }


def _build_warnings(
    selected_counts: list[dict[str, Any]],
    exclusion_counts: dict[str, Any],
    duplicate_checks: dict[str, int],
) -> list[str]:
    warnings: list[str] = []
    expected = {
        (role, str(label)): count
        for role, labels in _string_key_target_counts().items()
        for label, count in labels.items()
    }
    actual = {
        (str(row["role"]), str(row["label_binary"])): int(row["rows"])
        for row in selected_counts
    }
    for key, expected_count in expected.items():
        if actual.get(key) != expected_count:
            warnings.append(f"target count mismatch for {key}: expected {expected_count}, got {actual.get(key)}")
    for name, count in duplicate_checks.items():
        if count:
            warnings.append(f"{name}={count}")
    if exclusion_counts["selected_attack_from_limited_source"] != SOURCE_ATTACK_LIMIT_REQUESTED:
        warnings.append(
            "Requested source-specific attack limit conflicts with global target when existing TRAIN attack rows are preserved: "
            f"requested {SOURCE_ATTACK_LIMIT_REQUESTED}, selected {exclusion_counts['selected_attack_from_limited_source']}."
        )
    return warnings


def _render_markdown_report(payload: dict[str, Any]) -> str:
    return (
        "# DNS supervised 70/30 split rebuild\n\n"
        f"- Status: `{payload['status']}`\n"
        f"- Policy: `{payload['policy_id']}`\n"
        f"- Experiment: `{payload['experiment_id']}`\n"
        f"- Dry run: `{payload['dry_run']}`\n"
        f"- Apply catalog: `{payload['apply_catalog']}`\n\n"
        "## Target counts\n\n"
        f"```json\n{json.dumps(payload['target_counts'], indent=2, sort_keys=True)}\n```\n\n"
        "## Selected counts\n\n"
        f"```json\n{json.dumps(payload['selected_counts'], indent=2, sort_keys=True)}\n```\n\n"
        "## Exclusions\n\n"
        f"```json\n{json.dumps(payload['exclusion_counts'], indent=2, sort_keys=True)}\n```\n\n"
        "## Duplicate checks\n\n"
        f"```json\n{json.dumps(payload['duplicate_checks'], indent=2, sort_keys=True)}\n```\n\n"
        "## Catalog impact\n\n"
        f"```json\n{json.dumps(payload['catalog_impact'], indent=2, sort_keys=True)}\n```\n\n"
        "## Output artifacts\n\n"
        f"```json\n{json.dumps(payload['output_artifacts'], indent=2, sort_keys=True)}\n```\n\n"
        "## Warnings\n\n"
        f"{_markdown_list(payload.get('warnings') or ['none'])}\n"
    )


def _markdown_list(values: list[str]) -> str:
    return "\n".join(f"- `{value}`" for value in values)


def _fetch_dicts(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    rows = con.execute(sql).fetchall()
    columns = [description[0] for description in con.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def _create_id_table(con: duckdb.DuckDBPyConnection, name: str, ids: list[int]) -> None:
    con.execute(f"CREATE TEMP TABLE {name}(id BIGINT)")
    if ids:
        values = ", ".join(f"({int(value)})" for value in sorted(set(ids)))
        con.execute(f"INSERT INTO {name} VALUES {values}")


def _dataset_file_ids_for_path(session: Session, path: str) -> list[int]:
    return [
        int(file_id)
        for file_id in session.execute(select(DatasetFile.id).where(DatasetFile.file_path == path)).scalars()
    ]


def _normalized_ids_for_files(session: Session, file_ids: list[int]) -> list[int]:
    if not file_ids:
        return []
    return [
        int(artifact_id)
        for artifact_id in session.execute(
            select(NormalizedArtifact.id).where(NormalizedArtifact.file_id.in_(sorted(set(file_ids))))
        ).scalars()
    ]


def _target_total_for_label(label: int) -> int:
    return sum(counts[label] for counts in TARGET_COUNTS.values())


def _string_key_target_counts() -> dict[str, dict[str, int]]:
    return {
        role: {str(label): count for label, count in labels.items()}
        for role, labels in TARGET_COUNTS.items()
    }


def _target_distribution_for_role(role: str) -> dict[str, int] | None:
    labels = TARGET_COUNTS.get(role)
    if labels is None:
        return None
    return {str(label): count for label, count in labels.items()}


def _ensure_can_write(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(f"output artifact already exists; pass --overwrite to replace it: {path}")


def _report_dir(storage_root: Path) -> Path:
    configured = Path(REPORTS_RU_STAGE_THREE)
    if configured.is_absolute():
        return configured
    return storage_root / configured


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _sql_string(value: str) -> str:
    return value.replace("'", "''")
