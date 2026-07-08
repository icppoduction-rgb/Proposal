"""CLI route handlers for Stage Three feature/model-ready preparation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
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
from scripts.stage_three.labels.report import save_label_alignment_reports
from scripts.stage_three.labels.runner import run_label_alignment
from scripts.stage_three.model_ready.builder import build_model_ready_artifacts
from scripts.stage_three.model_ready.sequence_builder import (
    build_sequence_windows,
    save_sequence_builder_reports,
)
from scripts.stage_three.model_ready.report import save_model_ready_builder_reports
from scripts.stage_three.dns_rebalance import (
    DnsRebalanceRequest,
    run_dns_supervised_rebalance,
)
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
    RebalanceDnsSupervisedRequest,
    RunLeakageChecksRequest,
    RunQualityChecksRequest,
    StageThreeBaseRequest,
    TraceArtifactRequest,
    ValidateInputsRequest,
)
from scripts.stage_three.runtime.backend import select_feature_extraction_backend
from scripts.stage_three.reports.console import (
    BLOCKED_BY_ML_SAFETY,
    StageThreeConsoleReporter,
    format_duration,
    leakage_table,
    quality_table,
)
from scripts.stage_three.runtime.memory_guard import MemoryGuard
from scripts.stage_three.runtime.report import RuntimeBackendReport, save_runtime_backend_reports
from scripts.stage_three.runtime.resources import (
    RESOURCE_PROFILE_NAMES,
    StageThreeRuntimeSettings,
    resolve_stage_three_runtime_settings,
)
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
    "rebalance-dns-supervised",
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
        "rebalance-dns-supervised",
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
        elif isinstance(request, AlignLabelsRequest) and not request.dry_run:
            _run_align_labels(request)
        elif isinstance(request, BuildSequencesRequest) and not request.dry_run:
            _run_build_sequences(request)
        elif isinstance(request, BuildModelReadyRequest) and not request.dry_run:
            _run_build_model_ready(request)
        elif isinstance(request, RebalanceDnsSupervisedRequest):
            _run_rebalance_dns_supervised(request)
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
        fallback_request = locals().get("request")
        if fallback_request is None:
            fallback_request = StageThreeBaseRequest(
                command=str(service or "unknown"),
                json_output=bool(getattr(namespace, "json_output", False)),
                verbose=bool(getattr(namespace, "verbose", False)),
                quiet=bool(getattr(namespace, "quiet", False)),
            )
        StageThreeConsoleReporter(fallback_request, storage_root=PATH_DATA_STORAGE).error(
            phase="argument_validation",
            error=exc,
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
    _add_output_flags(build_feature_catalog)

    probe_runtime_backend = subparsers.add_parser(
        "probe-runtime-backend",
        help="Resolve CPU/GPU feature extraction backend and memory guard settings.",
    )
    probe_runtime_backend.add_argument("--backend", default="auto", choices=("auto", "cpu", "gpu"))
    _add_profile_and_memory_args(probe_runtime_backend)
    probe_runtime_backend.add_argument("--skip-probe", action="store_true")
    probe_runtime_backend.add_argument("--dry-run", action="store_true")
    _add_output_flags(probe_runtime_backend)

    extract_features = subparsers.add_parser(
        "extract-features",
        help="Extract feature artifacts from normalized Parquet inputs.",
    )
    _add_branch_role(extract_features, required=True)
    extract_features.add_argument("--feature-group", required=True)
    extract_features.add_argument("--experiment-id")
    _add_profile_and_memory_args(extract_features)
    extract_features.add_argument("--workers", type=_positive_int_arg)
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

    rebalance_dns = subparsers.add_parser(
        "rebalance-dns-supervised",
        help="Dry-run or apply the DNS supervised 70/30 split rebuild.",
    )
    rebalance_dns.add_argument("--experiment-id", default="dns_rebalanced_70_30_v1")
    rebalance_dns.add_argument("--feature-group", default="dns_lexical")
    rebalance_dns.add_argument("--target", default="label_binary")
    rebalance_dns.add_argument("--preprocessing-profile", default="tree_unscaled")
    rebalance_dns.add_argument("--overwrite", action="store_true")
    rebalance_dns.add_argument("--apply", action="store_true")
    rebalance_dns.add_argument("--apply-catalog", action="store_true")
    rebalance_dns.add_argument("--deactivate-existing-experiment")
    rebalance_dns.add_argument("--dry-run", action="store_true")
    _add_output_flags(rebalance_dns)

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
    _add_output_flags(trace_artifact)

    final_report = subparsers.add_parser(
        "final-report",
        help="Generate the final Stage Three report.",
    )
    final_report.add_argument("--experiment-id", required=True)
    final_report.add_argument("--branch")
    final_report.add_argument("--dry-run", action="store_true")
    _add_output_flags(final_report)

    return parser


def _add_branch_role(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument("--branch", required=required)
    parser.add_argument("--role", required=required)


def _add_execution_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    _add_output_flags(parser)


def _add_profile_and_memory_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", choices=RESOURCE_PROFILE_NAMES)
    parser.add_argument("--batch-rows", type=_positive_int_arg)
    parser.add_argument("--reserved-ram-gb", type=_positive_int_arg)
    parser.add_argument("--soft-ram-limit-gb", type=_positive_int_arg)
    parser.add_argument("--hard-ram-limit-gb", type=_positive_int_arg)


def _add_check_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--branch")
    parser.add_argument("--role")
    parser.add_argument("--feature-group")
    parser.add_argument("--dry-run", action="store_true")
    _add_output_flags(parser)


def _add_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", dest="json_output", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quiet", action="store_true")


def _request_from_namespace(namespace: argparse.Namespace) -> StageThreeBaseRequest:
    command = _required_text(namespace.command, "command")
    dry_run = bool(getattr(namespace, "dry_run", False))
    resume = bool(getattr(namespace, "resume", False))
    base = _base_request_kwargs(namespace, command=command, dry_run=dry_run, resume=resume)

    if command == "validate-inputs":
        return ValidateInputsRequest(
            **base,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
        )
    if command == "build-feature-catalog":
        return BuildFeatureCatalogRequest(
            **base,
            feature_group=_optional_text(namespace.feature_group),
        )
    if command == "probe-runtime-backend":
        return ProbeRuntimeBackendRequest(
            **base,
            backend=_required_text(namespace.backend, "backend"),
            profile=_optional_text(namespace.profile),
            batch_rows=_optional_positive_int(namespace.batch_rows),
            reserved_ram_gb=_optional_positive_int(namespace.reserved_ram_gb),
            soft_ram_limit_gb=_optional_positive_int(namespace.soft_ram_limit_gb),
            hard_ram_limit_gb=_optional_positive_int(namespace.hard_ram_limit_gb),
            skip_probe=bool(namespace.skip_probe),
        )
    if command == "extract-features":
        return ExtractFeaturesRequest(
            **base,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
            feature_group=_required_text(namespace.feature_group, "feature-group"),
            experiment_id=_optional_text(namespace.experiment_id),
            profile=_optional_text(namespace.profile),
            batch_rows=_optional_positive_int(namespace.batch_rows),
            reserved_ram_gb=_optional_positive_int(namespace.reserved_ram_gb),
            soft_ram_limit_gb=_optional_positive_int(namespace.soft_ram_limit_gb),
            hard_ram_limit_gb=_optional_positive_int(namespace.hard_ram_limit_gb),
            workers=_optional_positive_int(namespace.workers),
        )
    if command == "align-labels":
        return AlignLabelsRequest(
            **base,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_role(namespace.role),
            label_policy=_required_text(namespace.label_policy, "label-policy"),
            experiment_id=_optional_text(namespace.experiment_id),
        )
    if command == "build-sequences":
        return BuildSequencesRequest(
            **base,
            branch=_normalize_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            feature_group=_optional_text(namespace.feature_group),
            experiment_id=_optional_text(namespace.experiment_id),
        )
    if command == "build-model-ready":
        return BuildModelReadyRequest(
            **base,
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
    if command == "rebalance-dns-supervised":
        return RebalanceDnsSupervisedRequest(
            **_base_request_kwargs(
                namespace,
                command=command,
                dry_run=not bool(namespace.apply) or dry_run,
                resume=resume,
            ),
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            feature_group=_required_text(namespace.feature_group, "feature-group"),
            target=_required_text(namespace.target, "target"),
            preprocessing_profile=_required_text(
                namespace.preprocessing_profile,
                "preprocessing-profile",
            ),
            overwrite=bool(namespace.overwrite),
            apply_catalog=bool(namespace.apply_catalog),
            deactivate_existing_experiment=_optional_text(namespace.deactivate_existing_experiment),
        )
    if command == "run-quality-checks":
        return RunQualityChecksRequest(
            **base,
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            branch=_normalize_optional_branch(namespace.branch),
            role=_normalize_optional_role(namespace.role),
            feature_group=_optional_text(namespace.feature_group),
        )
    if command == "run-leakage-checks":
        return RunLeakageChecksRequest(
            **base,
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
            **base,
            artifact_ref=artifact_ref,
            experiment_id=experiment_id,
        )
    if command == "final-report":
        return FinalReportRequest(
            **base,
            experiment_id=_required_text(namespace.experiment_id, "experiment-id"),
            branch=_normalize_optional_branch(namespace.branch),
        )
    raise ValueError(f"unknown Stage Three command: {command}")


def _base_request_kwargs(
    namespace: argparse.Namespace,
    *,
    command: str,
    dry_run: bool,
    resume: bool,
) -> dict[str, Any]:
    if bool(getattr(namespace, "quiet", False)) and bool(getattr(namespace, "verbose", False)):
        raise ValueError("--quiet and --verbose are mutually exclusive")
    return {
        "command": command,
        "dry_run": dry_run,
        "resume": resume,
        "json_output": bool(getattr(namespace, "json_output", False)),
        "verbose": bool(getattr(namespace, "verbose", False)),
        "quiet": bool(getattr(namespace, "quiet", False)),
    }


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
        else "extract-features is implemented; dry-run only validates routing and configuration."
        if isinstance(request, ExtractFeaturesRequest)
        else "align-labels is implemented; dry-run only validates routing and configuration."
        if isinstance(request, AlignLabelsRequest)
        else "build-sequences is implemented; dry-run only validates routing and configuration."
        if isinstance(request, BuildSequencesRequest)
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
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    payload = {
        "status": "DRY_RUN" if request.dry_run else "PLANNED",
        "request": asdict(request),
        "requires_database": request.command in COMMANDS_REQUIRING_DATABASE,
        "opens_database_session": False,
        "db_session_policy": "open a fresh session_scope inside the command implementation; do not share sessions between workers",
        "storage_root": PATH_DATA_STORAGE,
        "feature_catalog_path": STAGE_THREE_FEATURE_CATALOG_PATH,
        "message": message,
    }
    reporter.finish(
        payload,
        summary={
            "command": f"stage-three {request.command}",
            "status": payload["status"],
            "request": repr(asdict(request)),
            "requires_database": payload["requires_database"],
            "storage_root": PATH_DATA_STORAGE,
            "feature_catalog_path": STAGE_THREE_FEATURE_CATALOG_PATH,
            "message": message,
        },
    )


def _run_build_feature_catalog(request: BuildFeatureCatalogRequest) -> None:
    """Validate the feature catalog and write deterministic outputs."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start({"feature_catalog_path": STAGE_THREE_FEATURE_CATALOG_PATH})
    catalog = load_feature_catalog(STAGE_THREE_FEATURE_CATALOG_PATH)
    if request.feature_group:
        _validate_requested_feature_group(catalog, request.feature_group)
    result = validate_feature_catalog(catalog)
    snapshot_path = save_normalized_catalog_snapshot(catalog)
    result = save_feature_catalog_reports(replace(result, normalized_snapshot_path=str(snapshot_path)))
    payload = {
        **result.to_dict(),
        "request": asdict(request),
        "message": "Stage Three feature catalog validation completed.",
    }
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "catalog_version": result.catalog_version,
            "feature_group_count": result.feature_group_count,
            "feature_count": result.feature_count,
            "normalized_snapshot_path": result.normalized_snapshot_path,
            "report_paths": result.report_paths,
        },
    )
    if result.status == CATALOG_FAIL:
        raise SystemExit(1)


def _validate_requested_feature_group(catalog: dict[str, Any], feature_group: str) -> None:
    groups = catalog.get("feature_groups")
    if not isinstance(groups, dict) or feature_group not in groups:
        raise ValueError(f"feature-group is not defined in catalog: {feature_group}")


def _run_probe_runtime_backend(request: ProbeRuntimeBackendRequest) -> None:
    """Resolve feature extraction backend selection and write Task06 reports."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
    settings = resolve_stage_three_runtime_settings(
        profile_name=request.profile,
        backend=request.backend,
        batch_rows=request.batch_rows,
        reserved_ram_gb=request.reserved_ram_gb,
        soft_ram_limit_gb=request.soft_ram_limit_gb,
        hard_ram_limit_gb=request.hard_ram_limit_gb,
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
    payload = {
        **report.to_dict(),
        "request": asdict(request),
        "backend_selected": selection.selected_backend,
        "gpu_available": selection.gpu_availability.available,
        "fallback_reason": selection.fallback_reason,
        "peak_rss_gb": memory_snapshot.peak_rss_gb,
        "message": "Stage Three runtime backend probe completed.",
    }
    profile = settings.resource_profile
    reporter.finish(
        payload,
        summary={
            "status": report.status,
            "backend_selected": selection.selected_backend,
            "gpu_available": selection.gpu_availability.available,
            "fallback_reason": selection.fallback_reason,
            "profile": profile.name,
            "batch_rows": profile.batch_rows,
            "requested_workers": getattr(request, "workers", None),
            "effective_workers": profile.default_workers,
            "RAM guard": f"reserved={profile.reserved_ram_gb}GB, soft={profile.soft_ram_limit_gb}GB, hard={profile.hard_ram_limit_gb}GB",
            "report_paths": report.report_paths,
        },
    )


def _run_extract_features(request: ExtractFeaturesRequest) -> None:
    """Run implemented Stage Three feature extraction commands."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    skipped_feature_artifacts = []
    runtime_settings = resolve_stage_three_runtime_settings(
        profile_name=request.profile,
        reserved_ram_gb=request.reserved_ram_gb,
        soft_ram_limit_gb=request.soft_ram_limit_gb,
        hard_ram_limit_gb=request.hard_ram_limit_gb,
        batch_rows=request.batch_rows,
        backend="cpu",
    )
    if request.workers is not None:
        runtime_settings = _override_extract_workers(request.workers, runtime_settings)
    runtime_profile = runtime_settings.resource_profile
    reporter.start(
        {
            "backend": "cpu",
            "requested_workers": request.workers or runtime_profile.default_workers,
            "effective_workers": runtime_profile.default_workers,
            "batch_rows": runtime_profile.batch_rows,
            "RAM guard": f"reserved={runtime_profile.reserved_ram_gb}GB, soft={runtime_profile.soft_ram_limit_gb}GB, hard={runtime_profile.hard_ram_limit_gb}GB",
        }
    )
    try:
        reporter.progress_callback({"phase": "catalog_lookup", "status": "start"})
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
            reporter.progress_callback(
                {
                    "phase": "resume_scan",
                    "status": "start",
                    "total_artifacts": len(artifacts),
                }
            )
            artifacts, skipped_feature_artifacts = registry.filter_resume_inputs(
                repository,
                artifacts,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                resume=request.resume,
            )
            reporter.progress_callback(
                {
                    "phase": "resume_scan",
                    "status": "end",
                    "total_artifacts": len(artifacts) + len(skipped_feature_artifacts),
                    "resume_skipped_count": len(skipped_feature_artifacts),
                }
            )
    except SQLAlchemyError as exc:
        reporter.error(
            phase="catalog_lookup",
            error=exc,
            suggested_next_command="Start or fix PostgreSQL, then rerun validate-inputs for this branch/role.",
        )
        raise SystemExit(1) from exc
    try:
        if request.branch == "dns":
            result = run_dns_feature_extraction(
                artifacts=artifacts,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                run_id=request.experiment_id,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                runtime_settings=runtime_settings,
                on_progress=reporter.progress_callback,
            )
        else:
            result = run_host_network_feature_extraction(
                artifacts=artifacts,
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
                run_id=request.experiment_id,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                runtime_settings=runtime_settings,
                on_progress=reporter.progress_callback,
            )
    except (ValueError, OSError) as exc:
        reporter.error(phase="feature_compute", error=exc)
        raise SystemExit(1) from exc
    try:
        reporter.progress_callback({"phase": "artifact_registration", "status": "start"})
        with session_scope() as session:
            repository = ArtifactRepository(session)
            registry = FeatureArtifactRegistryService(storage_root=PATH_DATA_STORAGE)
            result, registration = registry.register_result(
                repository,
                result,
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                skipped=skipped_feature_artifacts,
            )
            reporter.progress_callback(
                {
                    "phase": "artifact_registration",
                    "status": "end",
                    "total_artifacts": len(result.output_feature_artifacts),
                }
            )
    except SQLAlchemyError as exc:
        reporter.error(
            phase="artifact_registration",
            error=exc,
            suggested_next_command="Fix PostgreSQL catalog registration and rerun extract-features with --resume.",
            report_written=False,
        )
        raise SystemExit(1) from exc
    if request.branch == "dns":
        result = save_dns_feature_extraction_reports(result)
    else:
        result = save_host_network_feature_extraction_reports(result)
    result = save_feature_artifact_registration_reports(result)
    output_bytes = _feature_output_bytes(result)
    elapsed = result.runtime_seconds or reporter.elapsed_seconds()
    rows_per_second = result.rows_read / elapsed if elapsed else 0.0
    gb_per_hour = (output_bytes / (1024**3)) / (elapsed / 3600) if elapsed and output_bytes else 0.0
    payload = {
        **result.to_dict(),
        "request": asdict(request),
        "registered_catalog_ids": registration.registered_catalog_ids,
        "output_parquet_bytes": output_bytes,
        "throughput": {
            "rows_per_second": round(rows_per_second, 2),
            "gb_per_hour": round(gb_per_hour, 2),
        },
        "bottleneck": _extract_bottleneck_summary(result, reporter.progress_summary()),
        "message": "Stage Three feature extraction completed.",
    }
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "elapsed": format_duration(elapsed),
            "input_artifacts": len(result.input_normalized_artifacts),
            "resume_skipped": result.resume_skipped_count,
            "rows_scanned": result.rows_read,
            "feature_rows_written": result.rows_written,
            "output_artifacts": len(result.output_feature_artifacts),
            "output_parquet_bytes": output_bytes,
            "requested_workers": request.workers or runtime_profile.default_workers,
            "effective_workers": result.runtime_stats.get("effective_workers"),
            "batch_rows": result.runtime_stats.get("configured_batch_rows"),
            "selected_columns": result.columns_created,
            "projected_columns": result.columns_created,
            "partial_failed_work_units": 0,
            "throughput": f"{rows_per_second:.0f} rows/sec, {gb_per_hour:.2f} GB/hour",
            "bottleneck": _extract_bottleneck_summary(result, reporter.progress_summary()),
            "phase_timings": reporter.progress_summary().get("phase_seconds", {}),
            "resource_snapshot": reporter.progress_summary().get("resource_snapshot", {}),
            "report_paths": result.report_paths,
        },
        next_command=_next_after_extract_features(request),
    )


def _override_extract_workers(
    workers: int,
    runtime_settings: StageThreeRuntimeSettings,
) -> StageThreeRuntimeSettings:
    normalized_workers = max(1, workers)
    profile = runtime_settings.resource_profile
    effective_workers = min(normalized_workers, profile.max_workers)
    return replace(
        runtime_settings,
        resource_profile=replace(profile, default_workers=effective_workers),
    )


def _run_align_labels(request: AlignLabelsRequest) -> None:
    """Run streaming label alignment summaries for feature artifacts."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
    try:
        with session_scope() as session:
            repository = ArtifactRepository(session)
            result = run_label_alignment(
                repository,
                branch=request.branch,
                role=request.role,
                policy=request.label_policy,
                storage_root=PATH_DATA_STORAGE,
            )
    except (SQLAlchemyError, ValueError, OSError) as exc:
        reporter.error(phase="label_alignment", error=exc)
        raise SystemExit(1) from exc

    result = save_label_alignment_reports(result)
    status = "WARN" if result.summary.get("warnings") else "SUCCESS"
    payload = {
        "status": status,
        "request": asdict(request),
        **result.summary,
        "warnings": [
            *result.summary.get("warnings", []),
            "missing label is not benign; unlabeled samples must be handled explicitly",
        ],
        "message": "Stage Three label alignment completed.",
    }
    reporter.finish(
        payload,
        summary={
            "status": status,
            "label_policy": request.label_policy,
            "input_feature_artifacts": result.summary["feature_artifact_count"],
            "processed_samples": result.summary["sample_count"],
            "label_status_distribution": result.summary.get("label_status_distribution", {}),
            "label_source_distribution": result.summary.get("label_source_distribution", {}),
            "unlabeled_count": result.summary["unlabeled_count"],
            "conflicting_label_count": result.summary.get("conflicting_count", 0),
            "warning": "missing label is not benign",
            "report_paths": result.summary["report_paths"],
        },
        next_command=_next_after_align_labels(request),
    )


def _run_build_sequences(request: BuildSequencesRequest) -> None:
    """Build sequence/window reports from successful feature artifacts."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
    if request.role is None:
        reporter.error(phase="sequence_build", error="build-sequences requires --role for execution")
        raise SystemExit(2)
    try:
        with session_scope() as session:
            repository = ArtifactRepository(session)
            feature_artifacts = repository.list_successful_feature_artifacts(
                branch=request.branch,
                role=request.role,
                feature_group=request.feature_group,
            )
            if not feature_artifacts:
                raise ValueError(
                    f"no successful feature_artifacts found for branch={request.branch}, "
                    f"role={request.role}, feature_group={request.feature_group or '*'}"
                )
            rows = _feature_artifact_rows(feature_artifacts, storage_root=PATH_DATA_STORAGE)
    except (SQLAlchemyError, ValueError, OSError) as exc:
        reporter.error(phase="sequence_build", error=exc)
        raise SystemExit(1) from exc

    try:
        result = build_sequence_windows(rows, branch=request.branch, role=request.role)
        result = save_sequence_builder_reports(result)
    except (ValueError, OSError) as exc:
        reporter.error(phase="sequence_build", error=exc)
        raise SystemExit(1) from exc

    payload = {
        **result.to_dict(),
        "request": asdict(request),
        "input_feature_artifacts": len(feature_artifacts),
        "processed_rows": len(rows),
        "message": "Stage Three sequence windows completed.",
    }
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "branch": result.branch,
            "role": result.role,
            "input_feature_artifacts": len(feature_artifacts),
            "processed_rows": len(rows),
            "number_of_sequences": len(result.windows),
            "label_distribution": result.label_distribution,
            "ordering_policy": result.ordering_policy,
            "report_paths": result.report_paths,
        },
        next_command=_next_after_build_sequences(request),
    )


def _run_build_model_ready(request: BuildModelReadyRequest) -> None:
    """Build and register final model-ready artifacts."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start({"preprocessing_fit_role": "TRAIN"})
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
        reporter.error(phase="model_ready_build", error=exc)
        raise SystemExit(1) from exc

    result = save_model_ready_builder_reports(result)
    model_ready_summary = _model_ready_console_summary(result)
    payload = {
        **result.to_dict(),
        "request": asdict(request),
        "preprocessing_fit_role": "TRAIN",
        "message": "Stage Three model-ready artifact build completed.",
    }
    if model_ready_summary["forbidden_columns_remaining_count"]:
        reporter.finish(payload, summary=model_ready_summary, severity="CRITICAL")
        raise SystemExit(1)
    reporter.finish(
        payload,
        summary=model_ready_summary,
        next_command=_next_after_build_model_ready(request),
    )


def _run_rebalance_dns_supervised(request: RebalanceDnsSupervisedRequest) -> None:
    """Run the DNS supervised split audit or apply the rebuild."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
    try:
        with session_scope() as session:
            result = run_dns_supervised_rebalance(
                session,
                DnsRebalanceRequest(
                    experiment_id=request.experiment_id,
                    feature_group=request.feature_group,
                    preprocessing_profile=request.preprocessing_profile,
                    target=request.target,
                    storage_root=PATH_DATA_STORAGE,
                    dry_run=request.dry_run,
                    overwrite=request.overwrite,
                    apply_catalog=request.apply_catalog,
                    deactivate_existing_experiment=request.deactivate_existing_experiment,
                ),
            )
    except (SQLAlchemyError, ValueError, OSError) as exc:
        reporter.error(phase="dns_rebalance", error=exc)
        raise SystemExit(1) from exc

    payload = {**result.to_dict(), "request": asdict(request), "message": "DNS supervised split rebalance completed."}
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "selected_counts": result.selected_counts,
            "duplicate_checks": result.duplicate_checks,
            "catalog_updates": result.catalog_updates,
            "output_artifacts": len(result.output_artifacts),
            "report_paths": result.report_paths,
        },
    )
    if result.status == "FAILED":
        raise SystemExit(1)


def _run_quality_checks(request: RunQualityChecksRequest) -> None:
    """Run Stage Three feature/preprocessing/model-ready quality checks."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
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
        reporter.error(phase="quality_checks", error=exc)
        raise SystemExit(1) from exc

    result = save_stage_three_quality_reports(result)
    payload = {**result.to_dict(), "request": asdict(request), "message": "Stage Three quality checks completed."}
    checks = [record.to_dict() for record in result.checks]
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "feature_artifact_count": result.feature_artifact_count,
            "model_ready_artifact_count": result.model_ready_artifact_count,
            "preprocessing_artifact_count": result.preprocessing_artifact_count,
            "blocking": "yes" if result.blocking_issues else "no",
            "quality_report_ids": result.quality_report_ids,
            "report_paths": result.report_paths,
        },
        tables=[quality_table(_checks_with_report_path(checks, result.report_paths))],
        next_command=_next_after_quality_checks(request, result.status),
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_leakage_checks(request: RunLeakageChecksRequest) -> None:
    """Run Stage Three leakage and traceability checks."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
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
        reporter.error(phase="leakage_checks", error=exc)
        raise SystemExit(1) from exc

    result = save_stage_three_leakage_reports(result)
    payload = {**result.to_dict(), "request": asdict(request), "message": "Stage Three leakage and traceability checks completed."}
    checks = [record.to_dict() for record in result.checks]
    severity = "CRITICAL" if _has_critical_check(checks) else None
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "blocking": "yes" if result.blocked_artifact_ids or result.missing_links else "no",
            "blocked_artifact_ids": result.blocked_artifact_ids,
            "missing_links": result.missing_links,
            "quality_report_ids": result.quality_report_ids,
            "report_paths": result.report_paths,
        },
        tables=[
            leakage_table(checks),
            quality_table(_checks_with_report_path(checks, result.report_paths), title="Leakage Checks"),
        ],
        next_command=_next_after_leakage_checks(request, result.status),
        severity=severity,
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_trace_artifact(request: TraceArtifactRequest) -> None:
    """Trace a model-ready artifact back to the raw catalog source."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
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
        reporter.error(phase="traceability_chain", error=exc)
        raise SystemExit(1) from exc

    payload = {
        "status": chain.status,
        "request": asdict(request),
        "chain": chain.to_dict(),
        "blocking_issues": chain.missing_links,
        "message": "Traceability chain resolved." if chain.status != FAIL else "Traceability chain has missing links.",
    }
    reporter.finish(
        payload,
        summary={
            "status": chain.status,
            "artifact_id": chain.model_ready_artifact_id,
            "missing_links": chain.missing_links,
            "raw_source_path": chain.raw_source_path,
        },
    )
    if chain.status == FAIL:
        raise SystemExit(1)


def _run_validate_inputs(request: ValidateInputsRequest) -> None:
    """Run the Stage Three readiness gate and stop downstream on blocking failures."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
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
    payload = {**result.to_dict(), "request": asdict(request), "message": "Stage Three input readiness gate completed."}
    reporter.finish(
        payload,
        summary={
            "status": result.status,
            "branch": result.branch,
            "role": result.role,
            "normalized_artifact_count": result.normalized_artifact_count,
            "blocking": "yes" if result.blocking_issues else "no",
            "blocking_issues": result.blocking_issues,
            "report_paths": result.report_paths,
        },
        next_command=_next_after_validate_inputs(request, result.status),
    )
    if result.status == FAIL:
        raise SystemExit(1)


def _run_final_report(request: FinalReportRequest) -> None:
    """Generate the final Stage Three report from catalog state."""
    reporter = StageThreeConsoleReporter(request, storage_root=PATH_DATA_STORAGE)
    reporter.start()
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
        payload = {**result.to_dict(), "request": asdict(request)}
        reporter.finish(
            payload,
            summary=_final_report_console_summary(result),
        )
        return
    except (ValueError, OSError) as exc:
        reporter.error(phase="final_report", error=exc)
        raise SystemExit(1) from exc

    payload = {**result.to_dict(), "request": asdict(request), "message": "Final Stage Three report completed."}
    reporter.finish(
        payload,
        summary=_final_report_console_summary(result),
    )


def _feature_output_bytes(result: Any) -> int:
    total = 0
    for artifact in getattr(result, "output_feature_artifacts", []):
        for part in getattr(artifact, "parts", []) or []:
            try:
                total += Path(part).stat().st_size
            except OSError:
                continue
    return total


def _extract_bottleneck_summary(result: Any, progress_summary: dict[str, Any] | None = None) -> str:
    phase_seconds = (progress_summary or {}).get("phase_seconds") or {}
    if phase_seconds:
        buckets = {
            "DB": float(phase_seconds.get("catalog_lookup", 0.0))
            + float(phase_seconds.get("artifact_registration", 0.0)),
            "read": float(phase_seconds.get("parquet_scan", 0.0)),
            "compute": float(phase_seconds.get("feature_compute", 0.0)),
            "write": float(phase_seconds.get("parquet_write", 0.0)),
            "resume": float(phase_seconds.get("resume_scan", 0.0)),
            "validation": float(phase_seconds.get("validation", 0.0)),
        }
        total = sum(buckets.values())
        if total > 0:
            ranked = sorted(
                ((name, seconds) for name, seconds in buckets.items() if seconds > 0),
                key=lambda item: item[1],
                reverse=True,
            )
            return ", ".join(f"{name} {seconds / total:.0%}" for name, seconds in ranked) or "unknown"
    stats = getattr(result, "runtime_stats", {}) or {}
    if int(stats.get("artifact_count", 0)) == 0 and int(getattr(result, "resume_skipped_count", 0)) > 0:
        return "resume 100%"
    batch_count = int(stats.get("batch_count", 0) or 0)
    if batch_count:
        return "unknown (read/compute/write phase timing not instrumented per batch)"
    return "unknown"


def _feature_artifact_rows(artifacts: list[Any], *, storage_root: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        for path in _feature_artifact_part_paths(artifact, storage_root=storage_root):
            table = pq.read_table(path)
            rows.extend(table.to_pylist())
    return rows


def _feature_artifact_part_paths(artifact: Any, *, storage_root: str) -> list[Path]:
    paths: list[Path] = []
    metadata = getattr(artifact, "metadata_json", None) or {}
    parts = metadata.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("path"), str):
                paths.append(_resolve_cli_storage_path(part["path"], storage_root=storage_root))
    if not paths:
        feature_path = _resolve_cli_storage_path(getattr(artifact, "feature_path"), storage_root=storage_root)
        if feature_path.is_file():
            paths.append(feature_path)
        elif feature_path.is_dir():
            paths.extend(sorted(feature_path.glob("*.parquet")))
    return [path for path in paths if path.exists()]


def _resolve_cli_storage_path(path: str, *, storage_root: str) -> Path:
    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved
    return Path(storage_root).expanduser() / resolved


def _model_ready_console_summary(result: Any) -> dict[str, Any]:
    artifacts = [
        artifact
        for role_result in result.role_results
        for artifact in role_result.artifacts
    ]
    paths_by_type = {f"{artifact.role}.{artifact.data_type}": artifact.artifact_path for artifact in artifacts}
    forbidden_columns = sorted(
        {
            column
            for role_result in result.role_results
            for column in role_result.x_columns
            if _is_forbidden_console_column(column)
        }
    )
    dropped_columns = [
        item
        for role_result in result.role_results
        for item in _role_dropped_columns(role_result)
    ]
    missing_roles = sorted(set(("TRAIN", "VALIDATION", "TEST")).difference(result.roles))
    warnings = list(result.warnings)
    if missing_roles:
        warnings.append(f"missing roles: {', '.join(missing_roles)}")
    return {
        "status": result.status,
        "roles_included": result.roles,
        "feature_groups_included": _model_ready_feature_groups(result),
        "preprocessing_profile": result.preprocessing_profile,
        "preprocessing_fit_role": "TRAIN",
        "artifact_paths": paths_by_type,
        "split_index_artifact_path": (
            result.split_index_artifact.artifact_path if result.split_index_artifact is not None else None
        ),
        "preprocessing_metadata_artifact_path": (
            result.preprocessing_metadata_artifact.artifact_path
            if result.preprocessing_metadata_artifact is not None
            else None
        ),
        "x_row_count": sum(role_result.x_row_count for role_result in result.role_results),
        "feature_count": result.feature_count,
        "y_label_distribution": {
            role_result.role: role_result.target_distribution for role_result in result.role_results
        },
        "excluded_forbidden_columns_count": len(dropped_columns),
        "forbidden_columns_remaining_count": len(forbidden_columns),
        "forbidden_columns_remaining": forbidden_columns,
        "skipped_columns": dropped_columns,
        "warnings": warnings,
        "report_paths": result.report_paths,
    }


def _role_dropped_columns(role_result: Any) -> list[str]:
    values: list[str] = []
    for item in getattr(role_result, "dropped_columns", []) or []:
        if isinstance(item, dict):
            name = item.get("name")
            reason = item.get("reason")
            values.append(f"{name}: {reason}" if reason else str(name))
        else:
            values.append(str(item))
    return values


def _model_ready_feature_groups(result: Any) -> list[str]:
    groups: set[str] = {
        str(role_result.feature_group)
        for role_result in result.role_results
        if getattr(role_result, "feature_group", None)
    }
    for role_result in result.role_results:
        for artifact in role_result.artifacts:
            text = str(artifact.artifact_path)
            parts = Path(text).parts
            for part in parts:
                if part.startswith("feature_group="):
                    groups.add(part.split("=", 1)[1])
    return sorted(groups) or ["*"]


def _is_forbidden_console_column(column: str) -> bool:
    lowered = column.lower()
    return lowered.startswith("label_") or lowered in {
        "source_path",
        "source_file_path",
        "raw_file_path",
        "dataset_name",
        "metadata_json",
        "raw_fields_json",
    }


def _checks_with_report_path(checks: list[dict[str, Any]], report_paths: dict[str, str]) -> list[dict[str, Any]]:
    report_path = report_paths.get("en") or next(iter(report_paths.values()), "")
    enriched = []
    for check in checks:
        copied = dict(check)
        details = dict(copied.get("details") or {})
        details.setdefault("report_path", report_path)
        copied["details"] = details
        enriched.append(copied)
    return enriched


def _has_critical_check(checks: list[dict[str, Any]]) -> bool:
    return any(check.get("severity") == "CRITICAL" for check in checks)


def _final_report_console_summary(result: Any) -> dict[str, Any]:
    model_ready = result.model_ready_artifact_summary or {}
    required = model_ready.get("required_artifacts") or model_ready.get("required_model_ready_artifacts") or {}
    return {
        "status": result.status,
        "experiment_id": result.experiment_id,
        "branch": result.branch,
        "quality_status": (result.quality_checks_summary or {}).get("status"),
        "leakage_status": (result.leakage_checks_summary or {}).get("status"),
        "traceability_status": (result.traceability_checks_summary or {}).get("status"),
        "required_model_ready_artifacts": required,
        "required_model_ready_artifacts_found_missing": _found_missing_summary(required),
        "final_stage_four_readiness": result.stage_four_readiness_status,
        "readiness_blockers": result.readiness_blockers,
        "RU report path": result.report_paths.get("ru"),
        "EN report path": result.report_paths.get("en"),
    }


def _found_missing_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"found": "unknown", "missing": "unknown"}
    found = value.get("found") or value.get("present") or value.get("available")
    missing = value.get("missing")
    return {"found": found if found is not None else "unknown", "missing": missing if missing is not None else []}


def _next_after_validate_inputs(request: ValidateInputsRequest, status: str) -> str | None:
    if status == FAIL:
        return f"Fix blocking readiness issues, then rerun python manage.py stage-three validate-inputs --branch {request.branch} --role {request.role}"
    return "python manage.py stage-three build-feature-catalog"


def _next_after_extract_features(request: ExtractFeaturesRequest) -> str:
    experiment = f" --experiment-id {request.experiment_id}" if request.experiment_id else ""
    return (
        "python manage.py stage-three align-labels "
        f"--branch {request.branch} --role {request.role} --label-policy explicit_only{experiment} --resume"
    )


def _next_after_align_labels(request: AlignLabelsRequest) -> str:
    experiment = f" --experiment-id {request.experiment_id}" if request.experiment_id else ""
    return f"python manage.py stage-three build-sequences --branch {request.branch} --role {request.role}{experiment} --resume"


def _next_after_build_sequences(request: BuildSequencesRequest) -> str | None:
    if not request.experiment_id:
        return None
    group = f" --feature-group {request.feature_group}" if request.feature_group else ""
    return (
        "python manage.py stage-three build-model-ready "
        f"--experiment-id {request.experiment_id} --branch {request.branch}{group} --resume"
    )


def _next_after_build_model_ready(request: BuildModelReadyRequest) -> str:
    return f"python manage.py stage-three run-quality-checks --experiment-id {request.experiment_id} --branch {request.branch}"


def _next_after_quality_checks(request: RunQualityChecksRequest, status: str) -> str | None:
    if status == FAIL:
        return None
    return f"python manage.py stage-three run-leakage-checks --experiment-id {request.experiment_id}"


def _next_after_leakage_checks(request: RunLeakageChecksRequest, status: str) -> str | None:
    if status == FAIL:
        return BLOCKED_BY_ML_SAFETY
    branch = f" --branch {request.branch}" if request.branch else ""
    return f"python manage.py stage-three final-report --experiment-id {request.experiment_id}{branch}"


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


def _positive_int_arg(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _optional_positive_int(value: int | None) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise ValueError("must be a positive integer")
    return value


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
