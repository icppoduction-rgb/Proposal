"""CLI route handlers for Stage Three feature/model-ready preparation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict, replace
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

try:
    from rich.console import Console
except ModuleNotFoundError:

    class Console:  # type: ignore[no-redef]
        """Minimal console fallback when rich is not installed."""

        def print(self, value: object) -> None:
            print(value)

from config import DATABASE_URL, PATH_DATA_STORAGE, STAGE_THREE_FEATURE_CATALOG_PATH
from scripts.db import session_scope
from scripts.db.models import ModelReadyArtifact
from scripts.db.models.constants import ACTIVE_DATASET_ROLE_VALUES, BRANCH_VALUES
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.feature_catalog.loader import (
    load_feature_catalog,
    save_normalized_catalog_snapshot,
)
from scripts.stage_three.feature_catalog.report import save_feature_catalog_reports
from scripts.stage_three.feature_catalog.validator import (
    FAIL as CATALOG_FAIL,
    validate_feature_catalog,
)
from scripts.stage_three.extraction.report import (
    save_feature_artifact_registration_reports,
    save_dns_feature_extraction_reports,
    save_host_network_feature_extraction_reports,
)
from scripts.stage_three.extraction.registry import (
    FEATURE_ARTIFACT_SCHEMA_VERSION,
    FeatureArtifactRegistryService,
)
from scripts.stage_three.extraction.runner import (
    fetch_dns_normalized_artifacts,
    fetch_normalized_artifacts,
    run_host_network_feature_extraction,
    run_dns_feature_extraction,
)
from scripts.stage_three.model_ready.builder import build_model_ready_artifacts
from scripts.stage_three.model_ready.report import save_model_ready_builder_reports
from scripts.stage_three.quality.report import save_stage_three_quality_reports
from scripts.stage_three.quality.runner import run_stage_three_quality_checks
from scripts.stage_three.quality.leakage import run_stage_three_leakage_checks
from scripts.stage_three.quality.leakage_report import save_stage_three_leakage_reports
from scripts.stage_three.quality.traceability import trace_model_ready_artifact
from scripts.stage_three.readiness.report import save_validate_inputs_reports
from scripts.stage_three.readiness.validator import (
    FAIL,
    ReadinessCheck,
    StageThreeReadinessResult,
    validate_stage_three_inputs,
)
from scripts.stage_three.reports.final_report import (
    generate_catalog_unavailable_final_report,
    generate_final_stage_three_report,
)
from scripts.stage_three.requests import (
    AlignLabelsRequest,
    BuildFeatureCatalogRequest,
    BuildModelReadyRequest,
    BuildSequencesRequest,
    ExtractFeaturesRequest,
    FinalReportRequest,
    ProbeRuntimeBackendRequest,
    RunLeakageChecksRequest,
    RunQualityChecksRequest,
    StageThreeBaseRequest,
    TraceArtifactRequest,
    ValidateInputsRequest,
)
from scripts.stage_three.runtime.backend import select_feature_extraction_backend
from scripts.stage_three.runtime.memory_guard import MemoryGuard
from scripts.stage_three.runtime.report import RuntimeBackendReport, save_runtime_backend_reports
from scripts.stage_three.runtime.resources import resolve_stage_three_runtime_settings
from sqlalchemy import select


console = Console()

STAGE_THREE_COMMANDS: tuple[str, ...] = (
    "validate-inputs",
    "build-feature-catalog",
    "probe-runtime-backend",
    "extract-features",
    "align-labels",
    "build-sequences",
    "build-model-ready",
    "run-quality-checks",
    "run-leakage-checks",
    "trace-artifact",
    "final-report",
)

COMMANDS_REQUIRING_DATABASE: frozenset[str] = frozenset(
    {
        "validate-inputs",
        "extract-features",
        "align-labels",
        "build-sequences",
        "build-model-ready",
        "run-quality-checks",
        "run-leakage-checks",
        "trace-artifact",
        "final-report",
    }
)

LABEL_POLICIES: tuple[str, ...] = (
    "explicit_only",
    "any_attack_in_window",
    "majority_label",
    "last_event_label",
    "weak_allowed_with_confidence",
)


def router_stage_three(
    service: str | None,
    action: str | None = None,
    *,
    extra_args: Sequence[str] | None = None,
) -> None:
    """Route Stage Three CLI service names to command skeletons."""
    command_args = _command_args(action, extra_args)
    parser = build_stage_three_parser()

    if service in {None, "", "-h", "--help"}:
        parser.print_help()
        return

    if service not in STAGE_THREE_COMMANDS:
        _print_unknown_stage_three_command(service)
        raise SystemExit(2)

    namespace = parser.parse_args([service, *command_args])
    try:
        request = _request_from_namespace(namespace)
        _validate_runtime_config(request)
        if isinstance(request, BuildFeatureCatalogRequest) and not request.dry_run:
            _run_build_feature_catalog(request)
        elif isinstance(request, ProbeRuntimeBackendRequest) and not request.dry_run:
            _run_probe_runtime_backend(request)
        elif isinstance(request, ExtractFeaturesRequest) and not request.dry_run:
            _run_extract_features(request)
        elif isinstance(request, BuildModelReadyRequest) and not request.dry_run:
            _run_build_model_ready(request)
        elif isinstance(request, RunQualityChecksRequest) and not request.dry_run:
            _run_quality_checks(request)
        elif isinstance(request, RunLeakageChecksRequest) and not request.dry_run:
            _run_leakage_checks(request)
        elif isinstance(request, TraceArtifactRequest) and not request.dry_run:
            _run_trace_artifact(request)
        elif isinstance(request, FinalReportRequest) and not request.dry_run:
            _run_final_report(request)
        elif isinstance(request, ValidateInputsRequest) and not request.dry_run:
            _run_validate_inputs(request)
        else:
            _print_command_skeleton(request)
    except ValueError as exc:
        console.print(
            {
                "service": f"stage-three {service}",
                "status": "ERROR",
                "error": str(exc),
            }
        )
        raise SystemExit(2) from exc


def build_stage_three_parser() -> argparse.ArgumentParser:
    """Build the Stage Three argparse parser without opening DB connections."""
    parser = argparse.ArgumentParser(
        prog="python manage.py stage-three",
        description="Stage Three feature extraction and model-ready dataset preparation commands.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    validate_inputs = subparsers.add_parser(
        "validate-inputs",
        help="Validate Stage Two normalized outputs and catalog readiness.",
    )
    _add_branch_role(validate_inputs, required=True)
    _add_execution_flags(validate_inputs)

    build_feature_catalog = subparsers.add_parser(
        "build-feature-catalog",
        help="Build or validate the Stage Three feature catalog contract.",
    )
    build_feature_catalog.add_argument("--feature-group")
    build_feature_catalog.add_argument("--dry-run", action="store_true")

    probe_runtime_backend = subparsers.add_parser(
        "probe-runtime-backend",
        help="Resolve CPU/GPU feature extraction backend and memory guard settings.",
    )
    probe_runtime_backend.add_argument("--backend", default="auto", choices=("auto", "cpu", "gpu"))
    probe_runtime_backend.add_argument("--profile")
    probe_runtime_backend.add_argument("--skip-probe", action="store_true")
    probe_runtime_backend.add_argument("--dry-run", action="store_true")

    extract_features = subparsers.add_parser(
        "extract-features",
        help="Extract feature artifacts from normalized Parquet inputs.",
    )
    _add_branch_role(extract_features, required=True)
    extract_features.add_argument("--feature-group", required=True)
    extract_features.add_argument("--experiment-id")
    _add_execution_flags(extract_features)

    align_labels = subparsers.add_parser(
        "align-labels",
        help="Align labels without adding label fields to model-ready X.",
    )
    _add_branch_role(align_labels, required=True)
    align_labels.add_argument("--label-policy", default="explicit_only", choices=LABEL_POLICIES)
    align_labels.add_argument("--experiment-id")
    _add_execution_flags(align_labels)

    build_sequences = subparsers.add_parser(
        "build-sequences",
        help="Build sequence/window artifacts for downstream DL models.",
    )
    build_sequences.add_argument("--branch", required=True)
    build_sequences.add_argument("--role")
    build_sequences.add_argument("--feature-group")
    build_sequences.add_argument("--experiment-id")
    _add_execution_flags(build_sequences)

    build_model_ready = subparsers.add_parser(
        "build-model-ready",
        help="Assemble split-safe X/y/metadata/traceability artifacts.",
    )
    build_model_ready.add_argument("--experiment-id", required=True)
    build_model_ready.add_argument("--branch", required=True)
    build_model_ready.add_argument("--role")
    build_model_ready.add_argument("--feature-group")
    build_model_ready.add_argument("--target", default="label_binary")
    build_model_ready.add_argument("--preprocessing-profile", default="tree_unscaled")
    build_model_ready.add_argument("--include-sequences", action="store_true")
    _add_execution_flags(build_model_ready)

    run_quality_checks = subparsers.add_parser(
        "run-quality-checks",
        help="Run Stage Three artifact quality checks.",
    )
    _add_check_args(run_quality_checks)

    run_leakage_checks = subparsers.add_parser(
        "run-leakage-checks",
        help="Run Stage Three leakage checks for features/model-ready artifacts.",
    )
    _add_check_args(run_leakage_checks)

    trace_artifact = subparsers.add_parser(
        "trace-artifact",
        help="Trace a feature/model-ready artifact back to normalized and raw sources.",
    )
    trace_artifact.add_argument("artifact_ref", nargs="?")
    trace_artifact.add_argument("--experiment-id")
    trace_artifact.add_argument("--dry-run", action="store_true")

    final_report = subparsers.add_parser(
        "final-report",
        help="Generate the final Stage Three report.",
    )
    final_report.add_argument("--experiment-id", required=True)
    final_report.add_argument("--branch")
    final_report.add_argument("--dry-run", action="store_true")

    return parser


def _add_branch_role(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument("--branch", required=required)
    parser.add_argument("--role", required=required)


def _add_execution_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")


def _add_check_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--branch")
    parser.add_argument("--role")
    parser.add_argument("--feature-group")
    parser.add_argument("--dry-run", action="store_true")


def _request_from_namespace(namespace: argparse.Namespace) -> StageThreeBaseRequest:
    command = _required_text(namespace.command, "command")
    dry_run = bool(getattr(namespace, "dry_run", False))
    resume = bool(getattr(namespace, "resume", False))

    if command == "validate-inputs":
        return ValidateInputsRequest(
            command=command,
            dry_run=dry_run,
            resume=resume,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
        )
    if command == "build-feature-catalog":
        return BuildFeatureCatalogRequest(
            command=command,
            dry_run=dry_run,
            feature_group=_optional_text(namespace.feature_group),
        )
    if command == "probe-runtime-backend":
        return ProbeRuntimeBackendRequest(
            command=command,
            dry_run=dry_run,
            backend=_required_text(namespace.backend, "backend"),
            profile=_optional_text(namespace.profile),
            skip_probe=bool(namespace.skip_probe),
        )
    if command == "extract-features":
        return ExtractFeaturesRequest(
            command=command,
            dry_run=dry_run,
            resume=resume,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
            feature_group=_required_text(namespace.feature_group, "feature-group"),
            experiment_id=_optional_text(namespace.experiment_id),
        )
    if command == "align-labels":
        return AlignLabelsRequest(
            command=command,
            dry_run=dry_run,
            resume=resume,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
            label_policy=_required_text(namespace.label_policy, "label-policy"),
            experiment_id=_optional_text(namespace.experiment_id),
        )
    if command == "build-sequences":
        return BuildSequencesRequest(
            command=command,
            dry_run=dry_run,
            resume=resume,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            feature_group=_optional_text(namespace.feature_group),
            experiment_id=_optional_text(namespace.experiment_id),
        )
    if command == "build-model-ready":
        return BuildModelReadyRequest(
            command=command,
            dry_run=dry_run,
            resume=resume,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            feature_group=_optional_text(namespace.feature_group),
            target=_required_text(namespace.target, "target"),
            preprocessing_profile=_required_text(
                namespace.preprocessing_profile,
                "preprocessing-profile",
            ),
            include_sequences=bool(namespace.include_sequences),
        )
    if command == "run-quality-checks":
        return RunQualityChecksRequest(
            command=command,
            dry_run=dry_run,
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            branch=_normalize_optional_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            feature_group=_optional_text(namespace.feature_group),
        )
    if command == "run-leakage-checks":
        return RunLeakageChecksRequest(
            command=command,
            dry_run=dry_run,
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            branch=_normalize_optional_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            feature_group=_optional_text(namespace.feature_group),
        )
    if command == "trace-artifact":
        artifact_ref = _optional_text(namespace.artifact_ref)
        experiment_id = _optional_text(namespace.experiment_id)
        if artifact_ref is None and experiment_id is None:
            raise ValueError("trace-artifact requires artifact_ref or --experiment-id")
        return TraceArtifactRequest(
            command=command,
            dry_run=dry_run,
            artifact_ref=artifact_ref,
            experiment_id=experiment_id,
        )
    if command == "final-report":
        return FinalReportRequest(
            command=command,
            dry_run=dry_run,
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            branch=_normalize_optional_branch(namespace.branch),
        )
    raise ValueError(f"unknown Stage Three command: {command}")


def _validate_runtime_config(request: StageThreeBaseRequest) -> None:
    if not PATH_DATA_STORAGE.strip():
        raise ValueError("PATH_DATA_STORAGE must be configured before running Stage Three CLI commands.")
    if request.command in COMMANDS_REQUIRING_DATABASE and not request.dry_run and not DATABASE_URL.strip():
        raise ValueError("DATABASE_URL must be configured for this Stage Three command.")


def _print_command_skeleton(request: StageThreeBaseRequest) -> None:
    message = (
        "validate-inputs readiness logic is implemented; dry-run only validates routing and configuration."
        if isinstance(request, ValidateInputsRequest)
        else "build-feature-catalog validation is implemented; dry-run only validates routing and configuration."
        if isinstance(request, BuildFeatureCatalogRequest)
        else "probe-runtime-backend selection is implemented; dry-run only validates routing and configuration."
        if isinstance(request, ProbeRuntimeBackendRequest)
        else "build-model-ready is implemented; dry-run only validates routing and configuration."
        if isinstance(request, BuildModelReadyRequest)
        else "run-quality-checks is implemented; dry-run only validates routing and configuration."
        if isinstance(request, RunQualityChecksRequest)
        else "run-leakage-checks is implemented; dry-run only validates routing and configuration."
        if isinstance(request, RunLeakageChecksRequest)
        else "trace-artifact is implemented; dry-run only validates routing and configuration."
        if isinstance(request, TraceArtifactRequest)
        else "final-report is implemented; dry-run only validates routing and configuration."
        if isinstance(request, FinalReportRequest)
        else "CLI route and typed request are registered; business logic is reserved for later Stage Three tasks."
    )
    console.print(
        {
            "service": f"stage-three {request.command}",
            "status": "DRY_RUN" if request.dry_run else "PLANNED",
            "request": asdict(request),
            "requires_database": request.command in COMMANDS_REQUIRING_DATABASE,
            "opens_database_session": False,
            "db_session_policy": "open a fresh session_scope inside the command implementation; do not share sessions between workers",
            "storage_root": PATH_DATA_STORAGE,
            "feature_catalog_path": STAGE_THREE_FEATURE_CATALOG_PATH,
            "message": message,
        }
    )


def _run_build_feature_catalog(request: BuildFeatureCatalogRequest) -> None:
    """Validate the feature catalog and write deterministic outputs."""
    catalog = load_feature_catalog(STAGE_THREE_FEATURE_CATALOG_PATH)
    if request.feature_group:
        _validate_requested_feature_group(catalog, request.feature_group)
    result = validate_feature_catalog(catalog)
    snapshot_path = save_normalized_catalog_snapshot(catalog)
    result = save_feature_catalog_reports(replace(result, normalized_snapshot_path=str(snapshot_path)))
    console.print(
        {
            "service": "stage-three build-feature-catalog",
            "status": result.status,
            "request": asdict(request),
            "catalog_version": result.catalog_version,
            "feature_group_count": result.feature_group_count,
            "feature_count": result.feature_count,
            "normalized_snapshot_path": result.normalized_snapshot_path,
            "report_paths": result.report_paths,
            "message": "Stage Three feature catalog validation completed.",
        }
    )
    if result.status == CATALOG_FAIL:
        raise SystemExit(1)


def _validate_requested_feature_group(catalog: dict[str, Any], feature_group: str) -> None:
    groups = catalog.get("feature_groups")
    if not isinstance(groups, dict) or feature_group not in groups:
        raise ValueError(f"feature-group is not defined in catalog: {feature_group}")


def _run_probe_runtime_backend(request: ProbeRuntimeBackendRequest) -> None:
    """Resolve feature extraction backend selection and write Task06 reports."""
    settings = resolve_stage_three_runtime_settings(
        profile_name=request.profile,
        backend=request.backend,
    )
    memory_guard = MemoryGuard(
        reserved_ram_gb=settings.resource_profile.reserved_ram_gb,
        soft_ram_limit_gb=settings.resource_profile.soft_ram_limit_gb,
        hard_ram_limit_gb=settings.resource_profile.hard_ram_limit_gb,
    )
    _, selection = select_feature_extraction_backend(
        settings=settings,
        run_probe=not request.skip_probe,
    )
    memory_snapshot = memory_guard.snapshot()
    report = save_runtime_backend_reports(
        RuntimeBackendReport(
            status="PASS",
            backend_selection=selection,
            runtime_settings=settings,
            memory_snapshot=memory_snapshot,
        )
    )
    console.print(
        {
            "service": "stage-three probe-runtime-backend",
            "status": report.status,
            "request": asdict(request),
            "backend_selected": selection.selected_backend,
            "gpu_available": selection.gpu_availability.available,
            "fallback_reason": selection.fallback_reason,
            "peak_rss_gb": memory_snapshot.peak_rss_gb,
            "report_paths": report.report_paths,
            "message": "Stage Three runtime backend probe completed.",
        }
    )


def _run_extract_features(request: ExtractFeaturesRequest) -> None:
    """Run implemented Stage Three feature extraction commands."""
    skipped_feature_artifacts = []
    try:
        with session_scope() as session:
            if request.branch == "dns":
                artifacts = fetch_dns_normalized_artifacts(
                    session,
                    branch=request.branch,
                    role=request.role,
                )
            elif request.branch in {"host", "network"}:
                artifacts = fetch_normalized_artifacts(
                    session,
                    branch=request.branch,
                    role=request.role,
                )
            else:
                raise ValueError("extract-features supports --branch dns, host, or network")
            repository = ArtifactRepository(session)
            registry = FeatureArtifactRegistryService(storage_root=PATH_DATA_STORAGE)
            artifacts, skipped_feature_artifacts = registry.filter_resume_inputs(
                repository,
                artifacts,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                resume=request.resume,
            )
    except SQLAlchemyError as exc:
        console.print(
            {
                "service": "stage-three extract-features",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "PostgreSQL catalog is not reachable; DNS feature artifacts were not extracted.",
            }
        )
        raise SystemExit(1) from exc
    if request.branch == "dns":
        result = run_dns_feature_extraction(
            artifacts=artifacts,
            branch=request.branch,
            role=request.role,
            feature_group=request.feature_group,
            run_id=request.experiment_id,
            schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
        )
    else:
        result = run_host_network_feature_extraction(
            artifacts=artifacts,
            branch=request.branch,
            role=request.role,
            feature_group=request.feature_group,
            run_id=request.experiment_id,
            schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
        )
    try:
        with session_scope() as session:
            repository = ArtifactRepository(session)
            registry = FeatureArtifactRegistryService(storage_root=PATH_DATA_STORAGE)
            result, registration = registry.register_result(
                repository,
                result,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                skipped=skipped_feature_artifacts,
            )
    except SQLAlchemyError as exc:
        console.print(
            {
                "service": "stage-three extract-features",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Feature Parquet artifacts were written, but PostgreSQL catalog registration failed.",
            }
        )
        raise SystemExit(1) from exc
    if request.branch == "dns":
        result = save_dns_feature_extraction_reports(result)
    else:
        result = save_host_network_feature_extraction_reports(result)
    result = save_feature_artifact_registration_reports(result)
    console.print(
        {
            "service": "stage-three extract-features",
            "status": result.status,
            "request": asdict(request),
            "input_normalized_artifacts": len(result.input_normalized_artifacts),
            "output_feature_artifacts": len(result.output_feature_artifacts),
            "rows_read": result.rows_read,
            "rows_written": result.rows_written,
            "columns_created": result.columns_created,
            "registered_catalog_ids": registration.registered_catalog_ids,
            "resume_skipped_count": result.resume_skipped_count,
            "warnings": result.warnings,
            "runtime_stats": result.runtime_stats,
            "report_paths": result.report_paths,
            "message": "Stage Three feature extraction completed.",
        }
    )


def _run_build_model_ready(request: BuildModelReadyRequest) -> None:
    """Build and register final model-ready artifacts."""
    try:
        with session_scope() as session:
            repository = ArtifactRepository(session)
            result = build_model_ready_artifacts(
                repository,
                experiment_id=request.experiment_id,
                branch=request.branch,
                preprocessing_profile=request.preprocessing_profile,
                target=request.target,
                role=request.role,
                feature_group=request.feature_group,
                storage_root=PATH_DATA_STORAGE,
                resume=request.resume,
                include_sequences=request.include_sequences,
            )
    except (SQLAlchemyError, ValueError) as exc:
        console.print(
            {
                "service": "stage-three build-model-ready",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Model-ready artifacts were not completed.",
            }
        )
        raise SystemExit(1) from exc

    result = save_model_ready_builder_reports(result)
    console.print(
        {
            "service": "stage-three build-model-ready",
            "status": result.status,
            "request": asdict(request),
            "roles": result.roles,
            "feature_count": result.feature_count,
            "x_schema": result.x_schema,
            "artifacts": [
                artifact.to_dict()
                for role_result in result.role_results
                for artifact in role_result.artifacts
            ],
            "split_index_artifact": (
                result.split_index_artifact.to_dict()
                if result.split_index_artifact is not None
                else None
            ),
            "preprocessing_metadata_artifact": (
                result.preprocessing_metadata_artifact.to_dict()
                if result.preprocessing_metadata_artifact is not None
                else None
            ),
            "report_paths": result.report_paths,
            "message": "Stage Three model-ready artifact build completed.",
        }
    )


def _run_quality_checks(request: RunQualityChecksRequest) -> None:
    """Run Stage Three feature/preprocessing/model-ready quality checks."""
    try:
        with session_scope() as session:
            result = run_stage_three_quality_checks(
                session,
                experiment_id=request.experiment_id,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                storage_root=PATH_DATA_STORAGE,
            )
    except (SQLAlchemyError, ValueError, OSError) as exc:
        console.print(
            {
                "service": "stage-three run-quality-checks",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Stage Three quality checks were not completed.",
            }
        )
        raise SystemExit(1) from exc

    result = save_stage_three_quality_reports(result)
    console.print(
        {
            "service": "stage-three run-quality-checks",
            "status": result.status,
            "request": asdict(request),
            "feature_artifact_count": result.feature_artifact_count,
            "model_ready_artifact_count": result.model_ready_artifact_count,
            "preprocessing_artifact_count": result.preprocessing_artifact_count,
            "quality_report_ids": result.quality_report_ids,
            "blocking_issues": result.blocking_issues,
            "report_paths": result.report_paths,
            "message": "Stage Three quality checks completed.",
        }
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_leakage_checks(request: RunLeakageChecksRequest) -> None:
    """Run Stage Three leakage and traceability checks."""
    try:
        with session_scope() as session:
            result = run_stage_three_leakage_checks(
                session,
                experiment_id=request.experiment_id,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                storage_root=PATH_DATA_STORAGE,
            )
    except (SQLAlchemyError, ValueError, OSError) as exc:
        console.print(
            {
                "service": "stage-three run-leakage-checks",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Stage Three leakage checks were not completed.",
            }
        )
        raise SystemExit(1) from exc

    result = save_stage_three_leakage_reports(result)
    console.print(
        {
            "service": "stage-three run-leakage-checks",
            "status": result.status,
            "request": asdict(request),
            "quality_report_ids": result.quality_report_ids,
            "blocked_artifact_ids": result.blocked_artifact_ids,
            "missing_links": result.missing_links,
            "report_paths": result.report_paths,
            "message": "Stage Three leakage and traceability checks completed.",
        }
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_trace_artifact(request: TraceArtifactRequest) -> None:
    """Trace a model-ready artifact back to the raw catalog source."""
    try:
        with session_scope() as session:
            if request.artifact_ref is not None:
                artifact_id = _parse_artifact_id(request.artifact_ref)
            else:
                artifact_id = _first_model_ready_artifact_id_for_experiment(
                    session,
                    _required_text(request.experiment_id, "experiment-id"),
                )
            chain = trace_model_ready_artifact(
                session,
                artifact_id,
                apply_blocking_status=True,
            )
    except (SQLAlchemyError, ValueError) as exc:
        console.print(
            {
                "service": "stage-three trace-artifact",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Traceability chain was not resolved.",
            }
        )
        raise SystemExit(1) from exc

    console.print(
        {
            "service": "stage-three trace-artifact",
            "status": chain.status,
            "request": asdict(request),
            "chain": chain.to_dict(),
            "message": "Traceability chain resolved." if chain.status != FAIL else "Traceability chain has missing links.",
        }
    )
    if chain.status == FAIL:
        raise SystemExit(1)


def _run_validate_inputs(request: ValidateInputsRequest) -> None:
    """Run the Stage Three readiness gate and stop downstream on blocking failures."""
    try:
        with session_scope() as session:
            result = validate_stage_three_inputs(
                request,
                session,
                storage_root=PATH_DATA_STORAGE,
            )
    except SQLAlchemyError as exc:
        result = _database_failure_result(request, exc)
    result = save_validate_inputs_reports(result)
    console.print(
        {
            "service": "stage-three validate-inputs",
            "status": result.status,
            "request": asdict(request),
            "normalized_artifact_count": result.normalized_artifact_count,
            "blocking_issues": result.blocking_issues,
            "report_paths": result.report_paths,
            "message": "Stage Three input readiness gate completed.",
        }
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_final_report(request: FinalReportRequest) -> None:
    """Generate the final Stage Three report from catalog state."""
    try:
        with session_scope() as session:
            result = generate_final_stage_three_report(
                session,
                experiment_id=request.experiment_id,
                branch=request.branch,
                storage_root=PATH_DATA_STORAGE,
            )
    except SQLAlchemyError as exc:
        result = generate_catalog_unavailable_final_report(
            experiment_id=request.experiment_id,
            branch=request.branch,
            error=str(exc),
            storage_root=PATH_DATA_STORAGE,
        )
        console.print(
            {
                "service": "stage-three final-report",
                "status": result.status,
                "request": asdict(request),
                "stage_four_readiness_status": result.stage_four_readiness_status,
                "report_paths": result.report_paths,
                "documentation_files": result.documentation_files,
                "readiness_blockers": result.readiness_blockers,
                "message": "Final Stage Three report completed with catalog-unavailable blockers.",
            }
        )
        return
    except (ValueError, OSError) as exc:
        console.print(
            {
                "service": "stage-three final-report",
                "status": "ERROR",
                "request": asdict(request),
                "error": str(exc),
                "message": "Final Stage Three report was not completed.",
            }
        )
        raise SystemExit(1) from exc

    console.print(
        {
            "service": "stage-three final-report",
            "status": result.status,
            "request": asdict(request),
            "stage_four_readiness_status": result.stage_four_readiness_status,
            "report_paths": result.report_paths,
            "documentation_files": result.documentation_files,
            "readiness_blockers": result.readiness_blockers,
            "message": "Final Stage Three report completed.",
        }
    )


def _database_failure_result(
    request: ValidateInputsRequest,
    exc: SQLAlchemyError,
) -> StageThreeReadinessResult:
    message = "PostgreSQL catalog is not reachable; Stage Three inputs cannot be validated."
    check = ReadinessCheck(
        name="catalog_connection",
        status=FAIL,
        blocking=True,
        message=message,
        details={
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        },
    )
    return StageThreeReadinessResult(
        status=FAIL,
        branch=request.branch,
        role=request.role,
        checked_branches_roles=[{"branch": request.branch, "role": request.role}],
        normalized_artifact_count=0,
        normalized_artifacts_by_status={},
        parser_runs_by_status={},
        dataset_files_by_status={},
        checks=[check],
        blocking_issues=[message],
        next_actions=[
            "Do not start downstream Stage Three commands for this branch/role.",
            "Start or fix the PostgreSQL catalog connection, then rerun validate-inputs.",
        ],
    )


def _normalize_branch(value: str) -> str:
    normalized = _required_text(value, "branch").lower()
    if normalized not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"branch must be one of: {allowed}")
    return normalized


def _normalize_optional_branch(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return _normalize_branch(value)


def _normalize_role(value: str) -> str:
    normalized = _required_text(value, "role").upper()
    if normalized not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"role must be one of: {allowed}")
    return normalized


def _normalize_optional_role(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return _normalize_role(value)


def _required_text(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


def _parse_artifact_id(value: str) -> int:
    text = _required_text(value, "artifact_ref")
    try:
        artifact_id = int(text)
    except ValueError as exc:
        raise ValueError("trace-artifact currently expects a numeric model_ready_artifact_id") from exc
    if artifact_id <= 0:
        raise ValueError("model_ready_artifact_id must be positive")
    return artifact_id


def _first_model_ready_artifact_id_for_experiment(session: Any, experiment_id: str) -> int:
    statement = (
        select(ModelReadyArtifact.id)
        .where(ModelReadyArtifact.metadata_json["experiment_id"].as_string() == experiment_id)
        .order_by(ModelReadyArtifact.id.asc())
        .limit(1)
    )
    artifact_id = session.execute(statement).scalar_one_or_none()
    if artifact_id is None:
        raise ValueError(f"no model_ready_artifacts found for experiment_id={experiment_id}")
    return int(artifact_id)


def _command_args(action: str | None, extra_args: Sequence[str] | None) -> list[str]:
    args: list[str] = []
    if action:
        args.append(action)
    args.extend(extra_args or [])
    return args


def _print_unknown_stage_three_command(service: str | None) -> None:
    console.print(
        {
            "service": f"stage-three {service or ''}".strip(),
            "status": "ERROR",
            "error": "unknown Stage Three command",
            "available_commands": list(STAGE_THREE_COMMANDS),
        }
    )
