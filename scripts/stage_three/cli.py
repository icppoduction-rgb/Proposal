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
from scripts.db.models.constants import ACTIVE_DATASET_ROLE_VALUES, BRANCH_VALUES
from scripts.stage_three.feature_catalog.loader import (
    load_feature_catalog,
    save_normalized_catalog_snapshot,
)
from scripts.stage_three.feature_catalog.report import save_feature_catalog_reports
from scripts.stage_three.feature_catalog.validator import (
    FAIL as CATALOG_FAIL,
    validate_feature_catalog,
)
from scripts.stage_three.readiness.report import save_validate_inputs_reports
from scripts.stage_three.readiness.validator import (
    FAIL,
    ReadinessCheck,
    StageThreeReadinessResult,
    validate_stage_three_inputs,
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
