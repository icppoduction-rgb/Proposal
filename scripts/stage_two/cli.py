"""CLI route handlers for Stage Two data normalization services."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, replace
from typing import Any

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
except ModuleNotFoundError:
    BarColumn = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]

    class Console:  # type: ignore[no-redef]
        """Minimal console fallback when rich is not installed."""

        def print(self, value: object) -> None:
            print(value)

from config import manage_commands
from scripts.db import session_scope
from scripts.db.models.constants import (
    ACTIVE_CATALOG_SOURCE_GROUP,
    ACTIVE_DATASET_ROLE_VALUES,
    BRANCH_VALUES,
)
from scripts.db.repositories import DataQualityRepository, DatasetFileRepository
from scripts.stage_two.benchmark import (
    BenchmarkNormalizationRequest,
    benchmark_normalization,
    select_benchmark_files,
)
from scripts.stage_two.execution.format_policy import (
    FormatRuntimeFacts,
    format_runtime_facts_payload,
    resolve_format_policy,
)
from scripts.stage_two.normalization.runner import (
    NormalizeAllRequest,
    NormalizeAllRunner,
    NormalizeFormatRequest,
    NormalizeFormatRunner,
)
from scripts.stage_two.normalization.options import (
    NormalizationOptions,
    resolve_normalization_options,
    resource_profile_warning,
)
from scripts.stage_two.parser_coverage import ParserCoverageResult, run_parser_coverage
from scripts.stage_two.quality import validate_normalize_format_run
from scripts.stage_two.splitting import SplitLargeFilesRequest, SplitLargeFilesService
from scripts.stage_two.status_tools import MarkReadyRequest, MarkReadyService, save_mark_ready_reports


console = Console()

PLANNED_STAGE_TWO_COMMANDS: frozenset[str] = frozenset()


def router_stage_two(
    service: str | None,
    action: str | None = None,
    *,
    extra_args: Sequence[str] | None = None,
) -> None:
    """Route Stage Two CLI service names to implementation functions."""
    command_args = _command_args(action, extra_args)
    routes = {
        "bootstrap-storage": lambda args: _run_no_arg("bootstrap-storage", args, _bootstrap_storage),
        "catalog-ingest": lambda args: _run_no_arg("catalog-ingest", args, _catalog_ingest),
        "seed-parser-registry": lambda args: _run_no_arg(
            "seed-parser-registry",
            args,
            _seed_parser_registry,
        ),
        "parser-coverage": _parser_coverage,
        "mark-ready": _mark_ready,
        "normalize-format": _normalize_format,
        "normalize-all": _normalize_all,
        "benchmark-normalization": _benchmark_normalization,
        "split-large-files": _split_large_files,
        "normalize-dns": lambda args: _normalize_branch("dns", args),
        "normalize-host": lambda args: _normalize_branch("host", args),
        "run-duckdb-checks": lambda args: _run_no_arg(
            "run-duckdb-checks",
            args,
            _run_duckdb_checks,
        ),
        "run-leakage-checks": lambda args: _run_no_arg(
            "run-leakage-checks",
            args,
            _run_leakage_checks,
        ),
        "trace-artifact": _trace_artifact,
    }
    handler = routes.get(service or "")
    if handler is None:
        if service in PLANNED_STAGE_TWO_COMMANDS:
            _print_planned_command(service, command_args)
        else:
            _print_unknown_stage_two_command(service)
        return
    try:
        handler(command_args)
    except ValueError as exc:
        console.print(
            {
                "service": f"stage-two {service}",
                "status": "ERROR",
                "error": str(exc),
            },
        )


def _bootstrap_storage() -> None:
    from scripts.stage_two.storage.bootstrap import bootstrap_stage_two_storage

    result = bootstrap_stage_two_storage()
    console.print(
        {
            "service": "stage-two bootstrap-storage",
            "root": str(result.root),
            "created_count": len(result.created),
            "existing_count": len(result.existing),
        }
    )


def _catalog_ingest() -> None:
    from scripts.stage_two.ingestion.catalog_ingestion_service import CatalogIngestionService

    if Progress is None:
        with session_scope() as session:
            results = CatalogIngestionService(
                session,
                progress_callback=_print_catalog_ingest_progress,
            ).ingest_configured_roots()
    else:
        progress_tasks: dict[tuple[str, str, str], int] = {}
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            def progress_callback(event: str, payload: dict[str, Any]) -> None:
                _update_catalog_ingest_progress(progress, progress_tasks, event, payload)

            with session_scope() as session:
                results = CatalogIngestionService(
                    session,
                    progress_callback=progress_callback,
                ).ingest_configured_roots()

    console.print(
        {
            "service": "stage-two catalog-ingest",
            "runs": [asdict(result) for result in results],
            "run_count": len(results),
        }
    )


def _catalog_progress_task_key(payload: dict[str, Any], phase: str) -> tuple[str, str, str]:
    return (
        str(payload.get("root_kind") or ""),
        str(payload.get("root_path") or ""),
        phase,
    )


def _update_catalog_ingest_progress(
    progress: Any,
    progress_tasks: dict[tuple[str, str, str], int],
    event: str,
    payload: dict[str, Any],
) -> None:
    root_kind = str(payload.get("root_kind") or "catalog")
    root_path = str(payload.get("root_path") or "")

    if event == "root_skipped":
        reason = str(payload.get("reason") or "skipped")
        progress.add_task(f"{root_kind}: skipped ({reason})", total=1, completed=1)
        return

    if event == "scan_started":
        key = _catalog_progress_task_key(payload, "scan")
        progress_tasks[key] = progress.add_task(f"{root_kind}: scanning", total=1)
        return

    if event == "scan_finished":
        key = _catalog_progress_task_key(payload, "scan")
        task_id = progress_tasks.get(key)
        total = int(payload.get("total") or 0)
        description = f"{root_kind}: scanned {total} files"
        if task_id is None:
            progress.add_task(description, total=1, completed=1)
        else:
            progress.update(task_id, description=description, completed=1)
        return

    if event == "register_started":
        key = _catalog_progress_task_key(payload, "register")
        total = int(payload.get("total") or 0)
        progress_tasks[key] = progress.add_task(f"{root_kind}: registering", total=max(total, 1))
        if total == 0:
            progress.update(progress_tasks[key], completed=1)
        return

    if event in {"candidate_registered", "candidate_failed"}:
        key = _catalog_progress_task_key(payload, "register")
        task_id = progress_tasks.get(key)
        if task_id is None:
            return
        current = int(payload.get("current") or 0)
        total = int(payload.get("total") or 0)
        failed = int(payload.get("files_failed") or 0)
        description = f"{root_kind}: registering {current}/{total}"
        if failed:
            description = f"{description}, failed {failed}"
        progress.update(task_id, description=description, completed=max(current, 1))
        return

    if event == "bulk_upsert_started":
        key = _catalog_progress_task_key(payload, "upsert")
        row_count = int(payload.get("row_count") or 0)
        progress_tasks[key] = progress.add_task(
            f"{root_kind}: upserting {row_count} rows",
            total=1,
        )
        return

    if event == "bulk_upsert_finished":
        key = _catalog_progress_task_key(payload, "upsert")
        task_id = progress_tasks.get(key)
        row_count = int(payload.get("row_count") or 0)
        description = f"{root_kind}: upserted {row_count} rows"
        if task_id is None:
            progress.add_task(description, total=1, completed=1)
        else:
            progress.update(task_id, description=description, completed=1)
        return

    if event == "root_finished":
        status = str(payload.get("status") or "finished")
        files_seen = int(payload.get("files_seen") or 0)
        progress.add_task(f"{root_kind}: {status}, {files_seen} files", total=1, completed=1)
        return

    if event == "root_failed":
        error = str(payload.get("error") or "unknown error")
        location = f" ({root_path})" if root_path else ""
        progress.add_task(f"{root_kind}: failed{location}: {error}", total=1, completed=1)


def _print_catalog_ingest_progress(event: str, payload: dict[str, Any]) -> None:
    root_kind = str(payload.get("root_kind") or "catalog")
    if event == "root_skipped":
        console.print(
            {
                "service": "stage-two catalog-ingest",
                "event": event,
                "root_kind": root_kind,
                "reason": payload.get("reason"),
            }
        )
        return
    lifecycle_events = {
        "root_started",
        "scan_started",
        "scan_finished",
        "bulk_upsert_started",
        "bulk_upsert_finished",
        "root_finished",
        "root_failed",
    }
    if event in lifecycle_events:
        console.print({"service": "stage-two catalog-ingest", "event": event, **payload})
        return
    if event in {"candidate_registered", "candidate_failed"}:
        current = int(payload.get("current") or 0)
        total = int(payload.get("total") or 0)
        if current in {1, total} or current % 100 == 0:
            console.print({"service": "stage-two catalog-ingest", "event": event, **payload})


def _seed_parser_registry() -> None:
    from scripts.stage_two.parser_registry.seed import seed_stage_two_metadata

    result = seed_stage_two_metadata()
    console.print(
        {
            "service": "stage-two seed-parser-registry",
            "schema_version_id": result.schema_version_id,
            "schema_name": result.schema_name,
            "schema_version": result.schema_version,
            "inserted": result.parser_registry.inserted,
            "updated": result.parser_registry.updated,
        }
    )


def _parser_coverage(args: Sequence[str]) -> None:
    branch = _parse_optional_branch(args, service="parser-coverage")
    result = run_parser_coverage(branch=branch)
    _print_parser_coverage_table(result)
    console.print(
        {
            "service": "stage-two parser-coverage",
            "status": result.status,
            "branch": branch,
            "rows": len(result.matrix),
            "catalog_gap_rows": result.summary["catalog_gap_rows"],
            "report_paths": result.report_paths,
        }
    )


def _mark_ready(args: Sequence[str]) -> None:
    request = _parse_mark_ready_args(args)
    if Progress is None:
        with session_scope() as session:
            result = MarkReadyService(session).mark_ready(request)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            callback = _mark_ready_progress_callback(progress, request)
            with session_scope() as session:
                result = MarkReadyService(session, progress_callback=callback).mark_ready(request)
    result = save_mark_ready_reports(result)
    console.print(
        {
            "service": "stage-two mark-ready",
            **asdict(result),
        }
    )


def _normalize_format(args: Sequence[str]) -> None:
    request = _parse_normalize_format_args(args)
    if Progress is None:
        with session_scope() as session:
            request = _resolve_format_policy_for_request(session, request)
            _print_resolved_runtime_settings("normalize-format", request)
            result = NormalizeFormatRunner(session).normalize_format(request)
            validation = validate_normalize_format_run(session, request=request, result=result)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            callback = _normalize_progress_callback(progress)
            with session_scope() as session:
                request = _resolve_format_policy_for_request(session, request)
                _print_resolved_runtime_settings("normalize-format", request)
                result = NormalizeFormatRunner(session, progress_callback=callback).normalize_format(request)
                validation = validate_normalize_format_run(session, request=request, result=result)
    console.print(
        {
            "service": "stage-two normalize-format",
            **asdict(result),
            "post_run_validation": {
                "status": validation.status,
                "report_paths": validation.report_paths,
            },
        }
    )


def _normalize_all(args: Sequence[str]) -> None:
    request = _parse_normalize_all_args(args)
    _print_resolved_runtime_settings("normalize-all", request)
    if Progress is None:
        with session_scope() as session:
            result = NormalizeAllRunner(session).normalize_all(request)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            callback = _normalize_progress_callback(progress)
            with session_scope() as session:
                result = NormalizeAllRunner(session, progress_callback=callback).normalize_all(request)
    console.print(
        {
            "service": "stage-two normalize-all",
            **asdict(result),
        }
    )


def _benchmark_normalization(args: Sequence[str]) -> None:
    benchmark_request, normalize_request = _parse_benchmark_normalization_args(args)
    if Progress is None:
        with session_scope() as session:
            selected_files = select_benchmark_files(session, benchmark_request)
            normalize_request = replace(
                normalize_request,
                file_ids=tuple(file.file_id for file in selected_files),
                limit=None,
                resume=normalize_request.resume or not benchmark_request.dry_run,
            )
            normalize_request = _resolve_format_policy_for_request(session, normalize_request)
            _print_resolved_runtime_settings("benchmark-normalization", normalize_request)
            result = benchmark_normalization(
                session,
                benchmark_request=benchmark_request,
                normalize_request=normalize_request,
            )
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            callback = _normalize_progress_callback(progress)
            with session_scope() as session:
                selected_files = select_benchmark_files(session, benchmark_request)
                normalize_request = replace(
                    normalize_request,
                    file_ids=tuple(file.file_id for file in selected_files),
                    limit=None,
                    resume=normalize_request.resume or not benchmark_request.dry_run,
                )
                normalize_request = _resolve_format_policy_for_request(session, normalize_request)
                _print_resolved_runtime_settings("benchmark-normalization", normalize_request)
                result = benchmark_normalization(
                    session,
                    benchmark_request=benchmark_request,
                    normalize_request=normalize_request,
                    progress_callback=callback,
                )
    console.print(
        {
            "service": "stage-two benchmark-normalization",
            "status": result.status,
            "metrics": asdict(result.metrics),
            "report_paths": asdict(result.report_paths),
            "resume_forced": result.resume_forced,
        }
    )


def _split_large_files(args: Sequence[str]) -> None:
    request = _parse_split_large_files_args(args)
    with session_scope() as session:
        result = SplitLargeFilesService(session).split_large_files(request)
    console.print(
        {
            "service": "stage-two split-large-files",
            **asdict(result),
        }
    )


def _normalize_branch(branch: str, args: Sequence[str]) -> None:
    from scripts.stage_two.normalization.dns_service import DnsNormalizationService
    from scripts.stage_two.normalization.host_service import HostNormalizationService

    limit = _parse_optional_limit(args)
    service_class = DnsNormalizationService if branch == "dns" else HostNormalizationService

    with session_scope() as session:
        file_repository = DatasetFileRepository(session)
        files = file_repository.get_files_ready_for_parsing(
            branch=branch,
            limit=limit,
            source_group=ACTIVE_CATALOG_SOURCE_GROUP,
        )
        service = service_class(session)
        normalized = 0
        skipped = 0
        for dataset_file in files:
            artifact = service.normalize_file(dataset_file)
            if artifact is None:
                skipped += 1
            else:
                normalized += 1

    console.print(
        {
            "service": f"stage-two normalize-{branch}",
            "branch": branch,
            "limit": limit,
            "files_seen": len(files),
            "normalized": normalized,
            "skipped": skipped,
        }
    )


def _run_duckdb_checks() -> None:
    from scripts.stage_two.duckdb import DuckDBAnalyticsService

    analytics = DuckDBAnalyticsService()
    report = analytics.run_checks()
    with session_scope() as session:
        repository = DataQualityRepository(session)
        registered = analytics.register_report(repository, report)
    console.print(
        {
            "service": "stage-two run-duckdb-checks",
            "status": report.status,
            "report_path": report.report_path,
            "check_count": len(report.checks),
            "catalog_report_id": registered.id,
        }
    )


def _run_leakage_checks() -> None:
    from scripts.stage_two.duckdb import DuckDBAnalyticsService
    from scripts.stage_two.quality import LeakageChecker

    analytics = DuckDBAnalyticsService()
    with session_scope() as session:
        repository = DataQualityRepository(session)
        report = LeakageChecker(analytics, session=session).run(repository)
    console.print(
        {
            "service": "stage-two run-leakage-checks",
            "status": report.status,
            "severity": report.severity,
            "report_paths": report.report_paths,
            "check_count": len(report.checks),
        }
    )


def _trace_artifact(args: Sequence[str]) -> None:
    from scripts.stage_two.traceability import TraceabilityError, TraceabilityService

    artifact_ref = _parse_required_single_arg(
        args,
        service="trace-artifact",
        usage="python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>",
    )
    if not artifact_ref:
        console.print(
            {
                "service": "stage-two trace-artifact",
                "status": "ERROR",
                "usage": "python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>",
            }
        )
        return

    try:
        with session_scope() as session:
            service = TraceabilityService(session)
            chain = (
                service.get_by_model_ready_id(int(artifact_ref))
                if artifact_ref.isdecimal()
                else service.get_by_model_ready_path(artifact_ref)
            )
        console.print(json.dumps(asdict(chain), indent=2, sort_keys=True, default=_json_default))
    except TraceabilityError as exc:
        console.print(
            {
                "service": "stage-two trace-artifact",
                "status": "ERROR",
                "error": str(exc),
            }
        )


def _command_args(action: str | None, extra_args: Sequence[str] | None) -> list[str]:
    args: list[str] = []
    if action is not None:
        args.append(action)
    args.extend(extra_args or [])
    return args


def _mark_ready_progress_callback(progress: Any, request: MarkReadyRequest) -> Callable[[str, dict[str, Any]], None]:
    task_id: int | None = None

    def callback(event: str, payload: dict[str, Any]) -> None:
        nonlocal task_id
        if event not in {"file_seen", "file_marked_ready"}:
            return
        total = max(int(payload.get("total") or 1), 1)
        if task_id is None:
            mode = "retry failed" if request.retry_failed else "mark ready"
            task_id = progress.add_task(
                f"{mode}: {request.branch}/{request.role}/{request.source_format}",
                total=total,
            )
        progress.update(task_id, completed=int(payload.get("current") or 0), total=total)

    return callback


def _resolve_format_policy_for_request(session: Any, request: NormalizeFormatRequest) -> NormalizeFormatRequest:
    files = DatasetFileRepository(session).get_files_ready_for_parsing(
        branch=request.branch,
        role=request.role,
        source_format=request.source_format,
        limit=request.limit,
        file_ids=request.file_ids,
        source_group=ACTIVE_CATALOG_SOURCE_GROUP,
    )
    total_size = sum(int(file.file_size_bytes or 0) for file in files)
    facts = FormatRuntimeFacts(
        branch=request.branch,
        role=request.role,
        source_format=request.source_format,
        file_count=len(files),
        total_size_bytes=total_size,
        packet_mode=request.packet_mode,
    )
    base_options = NormalizationOptions(
        workers=request.workers,
        batch_size=request.batch_size,
        max_output_part_rows=request.max_output_part_rows,
        packet_batch_size=request.packet_batch_size,
        resume=request.resume,
        packet_mode=request.packet_mode,
        sample_size=request.sample_size,
        hash_outputs=request.hash_outputs,
        resource_profile=request.resource_profile,
        engine=request.engine,
    )
    decision = resolve_format_policy(
        base_options,
        facts,
        explicit_overrides=set(request.explicit_runtime_overrides),
    )
    options = decision.options
    return replace(
        request,
        workers=options.workers,
        batch_size=options.batch_size,
        max_output_part_rows=options.max_output_part_rows,
        packet_batch_size=options.packet_batch_size,
        packet_mode=options.packet_mode,
        hash_outputs=options.hash_outputs,
        engine=options.engine,
        format_policy=decision.policy_name,
        format_policy_warnings=decision.warnings,
        runtime_facts=format_runtime_facts_payload(facts),
    )


def _normalize_progress_callback(progress: Any) -> Callable[[str, dict[str, Any]], None]:
    task_id: int | None = None
    counters = {"parsed": 0, "partial": 0, "failed": 0, "skipped": 0}

    def callback(event: str, payload: dict[str, Any]) -> None:
        nonlocal task_id
        if event == "group_started":
            description = (
                f"group: {payload.get('branch')}/{payload.get('role')}/"
                f"{payload.get('source_format')}"
            )
            progress.add_task(description, total=1, completed=1)
            return
        if event == "batch_started":
            total = max(int(payload.get("total") or 1), 1)
            task_id = progress.add_task(
                (
                    f"normalize: {payload.get('branch')}/{payload.get('role')}/"
                    f"{payload.get('source_format')}"
                ),
                total=total,
            )
            counters.update({"parsed": 0, "partial": 0, "failed": 0, "skipped": 0})
            return
        if event != "file_processed" or task_id is None:
            return
        status = str(payload.get("status") or "")
        if status == "PARSED":
            counters["parsed"] += 1
        elif status == "PARTIALLY_PARSED":
            counters["partial"] += 1
        elif status == "FAILED":
            counters["failed"] += 1
        elif status in {"SKIPPED", "UNSUPPORTED_FORMAT"}:
            counters["skipped"] += 1
        description = (
            f"normalize parsed={counters['parsed']} partial={counters['partial']} "
            f"failed={counters['failed']} skipped={counters['skipped']}"
        )
        progress.update(
            task_id,
            description=description,
            completed=int(payload.get("current") or 0),
            total=max(int(payload.get("total") or 1), 1),
        )

    return callback


def _run_no_arg(service: str, args: Sequence[str], handler: Callable[[], None]) -> None:
    _require_no_args(service, args)
    handler()


def _require_no_args(service: str, args: Sequence[str]) -> None:
    if args:
        raise ValueError(f"{service} does not accept extra arguments: {' '.join(args)}")


def _parse_optional_limit(args: Sequence[str]) -> int | None:
    if not args:
        return None
    if len(args) > 1:
        raise ValueError(f"normalize accepts at most one limit argument, got: {' '.join(args)}")
    limit = args[0]
    if limit.isdecimal():
        return int(limit)
    raise ValueError("normalize action argument must be a non-negative integer limit when provided.")


def _parse_optional_branch(args: Sequence[str], *, service: str) -> str | None:
    if not args:
        return None
    if len(args) > 1:
        raise ValueError(f"{service} accepts at most one branch argument, got: {' '.join(args)}")
    branch = args[0].strip().lower()
    if branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"{service} branch must be one of: {allowed}")
    return branch


def _parse_mark_ready_args(args: Sequence[str]) -> MarkReadyRequest:
    if len(args) == 1 and ":" in args[0] and not args[0].startswith("--"):
        return _parse_mark_ready_fallback(args[0])

    values: dict[str, str] = {}
    apply_changes = False
    explicit_dry_run = False
    retry_failed = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--apply":
            apply_changes = True
            index += 1
            continue
        if arg == "--dry-run":
            explicit_dry_run = True
            index += 1
            continue
        if arg == "--retry-failed":
            retry_failed = True
            index += 1
            continue
        if arg in {"--branch", "--role", "--format"}:
            if index + 1 >= len(args) or args[index + 1].startswith("--"):
                raise ValueError(f"mark-ready requires a value for {arg}")
            values[arg] = args[index + 1]
            index += 2
            continue
        raise ValueError(
            "mark-ready accepts --branch, --role, --format, --dry-run, --apply, --retry-failed "
            "or fallback action:branch:role:format"
        )

    if apply_changes and explicit_dry_run:
        raise ValueError("mark-ready accepts only one execution mode: --dry-run or --apply")

    missing = [flag for flag in ("--branch", "--role", "--format") if flag not in values]
    if missing:
        raise ValueError(f"mark-ready missing required arguments: {', '.join(missing)}")

    return _build_mark_ready_request(
        branch=values["--branch"],
        role=values["--role"],
        source_format=values["--format"],
        apply_changes=apply_changes,
        retry_failed=retry_failed,
    )


def _parse_mark_ready_fallback(token: str) -> MarkReadyRequest:
    parts = token.split(":", 3)
    if len(parts) != 4:
        raise ValueError("mark-ready fallback format must be action:branch:role:format")
    action, branch, role, source_format = parts
    normalized_action = action.strip().lower()
    if normalized_action == "apply":
        apply_changes = True
    elif normalized_action == "dry-run":
        apply_changes = False
    else:
        raise ValueError("mark-ready fallback action must be apply or dry-run")
    return _build_mark_ready_request(
        branch=branch,
        role=role,
        source_format=source_format,
        apply_changes=apply_changes,
        retry_failed=False,
    )


def _build_mark_ready_request(
    *,
    branch: str,
    role: str,
    source_format: str,
    apply_changes: bool,
    retry_failed: bool = False,
) -> MarkReadyRequest:
    normalized_branch = branch.strip().lower()
    normalized_role = role.strip().upper()
    normalized_format = source_format.strip()
    if normalized_branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"mark-ready branch must be one of: {allowed}")
    if normalized_role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"mark-ready role must be one of: {allowed}")
    if not normalized_format:
        raise ValueError("mark-ready format must not be empty")
    return MarkReadyRequest(
        branch=normalized_branch,
        role=normalized_role,
        source_format=normalized_format,
        apply_changes=apply_changes,
        retry_failed=retry_failed,
    )


def _parse_normalize_format_args(args: Sequence[str]) -> NormalizeFormatRequest:
    if len(args) == 1 and ":" in args[0] and not args[0].startswith("--"):
        return _parse_normalize_format_fallback(args[0])

    values: dict[str, str] = {}
    flags: set[str] = set()
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {
            "--branch",
            "--role",
            "--format",
            "--limit",
            "--workers",
            "--batch-size",
            "--max-output-part-rows",
            "--packet-mode",
            "--sample-size",
            "--resource-profile",
            "--engine",
        }:
            if index + 1 >= len(args) or args[index + 1].startswith("--"):
                raise ValueError(f"normalize-format requires a value for {arg}")
            values[arg] = args[index + 1]
            index += 2
            continue
        if arg in {"--resume", "--hash-output-artifacts"}:
            flags.add(arg)
            index += 1
            continue
        raise ValueError(
            "normalize-format accepts --branch, --role, --format, --limit, --workers, "
            "--batch-size, --max-output-part-rows, --resume, --packet-mode, --sample-size, "
            "--resource-profile, --engine, "
            "--hash-output-artifacts "
            "or fallback branch:role:format:limit"
        )

    missing = [flag for flag in ("--branch", "--role", "--format") if flag not in values]
    if missing:
        raise ValueError(f"normalize-format missing required arguments: {', '.join(missing)}")

    return _build_normalize_format_request(
        branch=values["--branch"],
        role=values["--role"],
        source_format=values["--format"],
        limit=values.get("--limit"),
        workers=values.get("--workers"),
        batch_size=values.get("--batch-size"),
        max_output_part_rows=values.get("--max-output-part-rows"),
        resume="--resume" in flags,
        packet_mode=values.get("--packet-mode"),
        sample_size=values.get("--sample-size"),
        hash_outputs="--hash-output-artifacts" in flags,
        resource_profile=values.get("--resource-profile"),
        engine=values.get("--engine"),
        explicit_runtime_overrides=_explicit_runtime_overrides(values),
    )


def _parse_benchmark_normalization_args(
    args: Sequence[str],
) -> tuple[BenchmarkNormalizationRequest, NormalizeFormatRequest]:
    values: dict[str, str] = {}
    flags: set[str] = set()
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {
            "--branch",
            "--role",
            "--format",
            "--limit",
            "--sample-ratio",
            "--resource-profile",
            "--workers",
            "--batch-size",
            "--max-output-part-rows",
        }:
            if index + 1 >= len(args) or args[index + 1].startswith("--"):
                raise ValueError(f"benchmark-normalization requires a value for {arg}")
            values[arg] = args[index + 1]
            index += 2
            continue
        if arg in {"--resume", "--dry-run"}:
            flags.add(arg)
            index += 1
            continue
        raise ValueError(
            "benchmark-normalization accepts --branch, --role, --format, --limit, "
            "--sample-ratio, --resource-profile, --workers, --batch-size, "
            "--max-output-part-rows, --resume, --dry-run"
        )

    missing = [flag for flag in ("--branch", "--role", "--format") if flag not in values]
    if missing:
        raise ValueError(f"benchmark-normalization missing required arguments: {', '.join(missing)}")

    normalize_request = _build_normalize_format_request(
        branch=values["--branch"],
        role=values["--role"],
        source_format=values["--format"],
        limit=values.get("--limit"),
        workers=values.get("--workers"),
        batch_size=values.get("--batch-size"),
        max_output_part_rows=values.get("--max-output-part-rows"),
        resume="--resume" in flags,
        resource_profile=values.get("--resource-profile"),
        explicit_runtime_overrides=_explicit_runtime_overrides(values),
    )
    benchmark_request = BenchmarkNormalizationRequest(
        branch=normalize_request.branch,
        role=normalize_request.role,
        source_format=normalize_request.source_format,
        limit=normalize_request.limit,
        sample_ratio=_parse_sample_ratio(values.get("--sample-ratio")),
        dry_run="--dry-run" in flags,
        resume=normalize_request.resume,
    )
    return benchmark_request, normalize_request


def _parse_normalize_format_fallback(token: str) -> NormalizeFormatRequest:
    parts = token.split(":", 3)
    if len(parts) not in {3, 4}:
        raise ValueError("normalize-format fallback format must be branch:role:format[:limit]")
    branch, role, source_format = parts[:3]
    limit = parts[3] if len(parts) == 4 else None
    return _build_normalize_format_request(
        branch=branch,
        role=role,
        source_format=source_format,
        limit=limit,
    )


def _explicit_runtime_overrides(values: dict[str, str]) -> tuple[str, ...]:
    mapping = {
        "--workers": "workers",
        "--batch-size": "batch_size",
        "--max-output-part-rows": "max_output_part_rows",
        "--packet-mode": "packet_mode",
        "--engine": "engine",
    }
    return tuple(value for key, value in mapping.items() if key in values)


def _build_normalize_format_request(
    *,
    branch: str,
    role: str,
    source_format: str,
    limit: str | None,
    workers: str | None = None,
    batch_size: str | None = None,
    max_output_part_rows: str | None = None,
    resume: bool = False,
    packet_mode: str | None = None,
    sample_size: str | None = None,
    hash_outputs: bool = False,
    resource_profile: str | None = None,
    engine: str | None = None,
    explicit_runtime_overrides: tuple[str, ...] = (),
) -> NormalizeFormatRequest:
    normalized_branch = branch.strip().lower()
    normalized_role = role.strip().upper()
    normalized_format = source_format.strip()
    parsed_limit = _parse_normalize_format_limit(limit)
    if normalized_branch not in {"dns", "host"}:
        raise ValueError("normalize-format branch must be one of: dns, host")
    if normalized_role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"normalize-format role must be one of: {allowed}")
    if not normalized_format:
        raise ValueError("normalize-format format must not be empty")
    options = resolve_normalization_options(
        resource_profile=resource_profile,
        workers=_parse_positive_int(workers, field_name="workers", service="normalize-format"),
        batch_size=_parse_positive_int(batch_size, field_name="batch-size", service="normalize-format"),
        max_output_part_rows=_parse_positive_int(
            max_output_part_rows,
            field_name="max-output-part-rows",
            service="normalize-format",
        ),
        resume=resume,
        packet_mode=packet_mode.strip() if packet_mode else None,
        sample_size=_parse_positive_int(sample_size, field_name="sample-size", service="normalize-format"),
        hash_outputs=hash_outputs,
        engine=engine.strip().lower() if engine else None,
    )
    return NormalizeFormatRequest(
        branch=normalized_branch,
        role=normalized_role,
        source_format=normalized_format,
        limit=parsed_limit,
        workers=options.workers,
        batch_size=options.batch_size,
        max_output_part_rows=options.max_output_part_rows,
        packet_batch_size=options.packet_batch_size,
        resume=options.resume,
        packet_mode=options.packet_mode,
        sample_size=options.sample_size,
        hash_outputs=options.hash_outputs,
        resource_profile=options.resource_profile,
        engine=options.engine,
        explicit_runtime_overrides=explicit_runtime_overrides,
    )


def _parse_normalize_format_limit(limit: str | None) -> int | None:
    if limit is None or not limit.strip():
        return None
    normalized_limit = limit.strip()
    if normalized_limit.isdecimal():
        return int(normalized_limit)
    raise ValueError("normalize-format limit must be a non-negative integer")


def _parse_positive_int(value: str | None, *, field_name: str, service: str) -> int | None:
    if value is None or not value.strip():
        return None
    normalized_value = value.strip()
    if normalized_value.isdecimal() and int(normalized_value) > 0:
        return int(normalized_value)
    raise ValueError(f"{service} {field_name} must be a positive integer")


def _parse_sample_ratio(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        sample_ratio = float(value.strip())
    except ValueError as exc:
        raise ValueError("benchmark-normalization sample-ratio must be a number in (0, 1]") from exc
    if 0 < sample_ratio <= 1:
        return sample_ratio
    raise ValueError("benchmark-normalization sample-ratio must be in (0, 1]")


def _parse_split_large_files_args(args: Sequence[str]) -> SplitLargeFilesRequest:
    values: dict[str, str] = {}
    flags: set[str] = set()
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {
            "--branch",
            "--role",
            "--format",
            "--limit",
            "--max-part-size-gb",
            "--max-part-size-mb",
            "--min-size-gb",
            "--min-size-mb",
            "--header",
        }:
            if index + 1 >= len(args) or args[index + 1].startswith("--"):
                raise ValueError(f"split-large-files requires a value for {arg}")
            values[arg] = args[index + 1]
            index += 2
            continue
        if arg in {"--apply", "--register", "--overwrite", "--keep-source-ready"}:
            flags.add(arg)
            index += 1
            continue
        raise ValueError(
            "split-large-files accepts --branch, --role, --format, --limit, "
            "--max-part-size-gb/mb, --min-size-gb/mb, --header auto|yes|no, "
            "--apply, --register, --overwrite, --keep-source-ready"
        )

    missing = [flag for flag in ("--branch", "--role", "--format") if flag not in values]
    if missing:
        raise ValueError(f"split-large-files missing required arguments: {', '.join(missing)}")

    max_part_size_bytes = _parse_size_bytes(
        gb=values.get("--max-part-size-gb"),
        mb=values.get("--max-part-size-mb"),
        default_gb=2.0,
        field_name="max-part-size",
    )
    min_file_size_bytes = _parse_size_bytes(
        gb=values.get("--min-size-gb"),
        mb=values.get("--min-size-mb"),
        default_gb=1.0,
        field_name="min-size",
        allow_zero=True,
    )
    header = values.get("--header", "auto").strip().lower()
    if header not in {"auto", "yes", "no"}:
        raise ValueError("split-large-files header must be one of: auto, yes, no")

    normalized_branch = values["--branch"].strip().lower()
    normalized_role = values["--role"].strip().upper()
    normalized_format = values["--format"].strip()
    if normalized_branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"split-large-files branch must be one of: {allowed}")
    if normalized_role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"split-large-files role must be one of: {allowed}")
    if not normalized_format:
        raise ValueError("split-large-files format must not be empty")

    return SplitLargeFilesRequest(
        branch=normalized_branch,
        role=normalized_role,
        source_format=normalized_format,
        limit=_parse_positive_int(values.get("--limit"), field_name="limit", service="split-large-files"),
        max_part_size_bytes=max_part_size_bytes,
        min_file_size_bytes=min_file_size_bytes,
        apply_changes="--apply" in flags,
        register="--register" in flags,
        overwrite="--overwrite" in flags,
        keep_source_ready="--keep-source-ready" in flags,
        header_mode=header,  # type: ignore[arg-type]
    )


def _parse_size_bytes(
    *,
    gb: str | None,
    mb: str | None,
    default_gb: float,
    field_name: str,
    allow_zero: bool = False,
) -> int:
    if gb is not None and mb is not None:
        raise ValueError(f"split-large-files accepts only one of --{field_name}-gb or --{field_name}-mb")
    multiplier = 1024 * 1024 * 1024
    value = gb
    if mb is not None:
        multiplier = 1024 * 1024
        value = mb
    if value is None:
        return int(default_gb * 1024 * 1024 * 1024)
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"split-large-files {field_name} must be a number") from exc
    if number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"split-large-files {field_name} must be positive")
    return int(number * multiplier)


def _parse_normalize_all_args(args: Sequence[str]) -> NormalizeAllRequest:
    if len(args) == 1 and ":" in args[0] and not args[0].startswith("--"):
        return _parse_normalize_all_fallback(args[0])

    values: dict[str, str] = {}
    flags: set[str] = set()
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {
            "--branch",
            "--limit",
            "--workers",
            "--batch-size",
            "--max-output-part-rows",
            "--packet-mode",
            "--sample-size",
            "--resource-profile",
            "--engine",
        }:
            if index + 1 >= len(args) or args[index + 1].startswith("--"):
                raise ValueError(f"normalize-all requires a value for {arg}")
            values[arg] = args[index + 1]
            index += 2
            continue
        if arg in {"--resume", "--hash-output-artifacts"}:
            flags.add(arg)
            index += 1
            continue
        raise ValueError(
            "normalize-all accepts --branch, --limit, --workers, --batch-size, "
            "--max-output-part-rows, --resume, --packet-mode, --sample-size, "
            "--resource-profile, --engine, "
            "--hash-output-artifacts or fallback branch:limit"
        )

    if "--branch" not in values:
        raise ValueError("normalize-all missing required argument: --branch")

    return _build_normalize_all_request(
        branch=values["--branch"],
        limit=values.get("--limit"),
        workers=values.get("--workers"),
        batch_size=values.get("--batch-size"),
        max_output_part_rows=values.get("--max-output-part-rows"),
        resume="--resume" in flags,
        packet_mode=values.get("--packet-mode"),
        sample_size=values.get("--sample-size"),
        hash_outputs="--hash-output-artifacts" in flags,
        resource_profile=values.get("--resource-profile"),
        engine=values.get("--engine"),
    )


def _parse_normalize_all_fallback(token: str) -> NormalizeAllRequest:
    parts = token.split(":", 1)
    if len(parts) not in {1, 2}:
        raise ValueError("normalize-all fallback format must be branch[:limit]")
    branch = parts[0]
    limit = parts[1] if len(parts) == 2 else None
    return _build_normalize_all_request(branch=branch, limit=limit)


def _build_normalize_all_request(
    *,
    branch: str,
    limit: str | None,
    workers: str | None = None,
    batch_size: str | None = None,
    max_output_part_rows: str | None = None,
    resume: bool = False,
    packet_mode: str | None = None,
    sample_size: str | None = None,
    hash_outputs: bool = False,
    resource_profile: str | None = None,
    engine: str | None = None,
) -> NormalizeAllRequest:
    normalized_branch = branch.strip().lower()
    parsed_limit = _parse_normalize_all_limit(limit)
    if normalized_branch not in {"dns", "host"}:
        raise ValueError("normalize-all branch must be one of: dns, host")
    options = resolve_normalization_options(
        resource_profile=resource_profile,
        workers=_parse_positive_int(workers, field_name="workers", service="normalize-all"),
        batch_size=_parse_positive_int(batch_size, field_name="batch-size", service="normalize-all"),
        max_output_part_rows=_parse_positive_int(
            max_output_part_rows,
            field_name="max-output-part-rows",
            service="normalize-all",
        ),
        resume=resume,
        packet_mode=packet_mode.strip() if packet_mode else None,
        sample_size=_parse_positive_int(sample_size, field_name="sample-size", service="normalize-all"),
        hash_outputs=hash_outputs,
        engine=engine.strip().lower() if engine else None,
    )
    return NormalizeAllRequest(
        branch=normalized_branch,
        limit=parsed_limit,
        workers=options.workers,
        batch_size=options.batch_size,
        max_output_part_rows=options.max_output_part_rows,
        packet_batch_size=options.packet_batch_size,
        resume=options.resume,
        packet_mode=options.packet_mode,
        sample_size=options.sample_size,
        hash_outputs=options.hash_outputs,
        resource_profile=options.resource_profile,
        engine=options.engine,
    )


def _parse_normalize_all_limit(limit: str | None) -> int | None:
    if limit is None or not limit.strip():
        return None
    normalized_limit = limit.strip()
    if normalized_limit.isdecimal():
        return int(normalized_limit)
    raise ValueError("normalize-all limit must be a non-negative integer")


def _parse_required_single_arg(args: Sequence[str], *, service: str, usage: str) -> str | None:
    if not args:
        return None
    if len(args) > 1:
        raise ValueError(f"{service} accepts exactly one argument. Usage: {usage}")
    return args[0]


def _print_planned_command(service: str, args: Sequence[str]) -> None:
    console.print(
        {
            "service": f"stage-two {service}",
            "status": "NOT_IMPLEMENTED",
            "args": list(args),
            "message": "CLI route is reserved for a later task; business logic is not implemented yet.",
        }
    )


def _print_unknown_stage_two_command(service: str | None) -> None:
    console.print(
        {
            "service": f"stage-two {service or ''}".strip(),
            "status": "ERROR",
            "error": "unknown Stage Two command",
        }
    )
    console.print(manage_commands)


def _runtime_settings_payload(
    service: str,
    request: NormalizeFormatRequest | NormalizeAllRequest,
) -> dict[str, Any]:
    warning = resource_profile_warning(request.resource_profile)
    payload: dict[str, Any] = {
        "service": f"stage-two {service}",
        "event": "resolved_runtime_settings",
        "resource_profile": request.resource_profile or "default",
        "format_policy": getattr(request, "format_policy", None),
        "workers": request.workers,
        "batch_size": request.batch_size,
        "max_output_part_rows": request.max_output_part_rows,
        "packet_batch_size": request.packet_batch_size,
        "packet_mode": request.packet_mode,
        "engine": request.engine,
        "sample_size": request.sample_size,
        "resume": request.resume,
        "hash_output_artifacts": request.hash_outputs,
    }
    if isinstance(request, NormalizeFormatRequest):
        payload.update(
            {
                "branch": request.branch,
                "role": request.role,
                "source_format": request.source_format,
                "limit": request.limit,
                "runtime_facts": request.runtime_facts,
                "format_policy_warnings": request.format_policy_warnings,
            }
        )
    else:
        payload.update(
            {
                "branch": request.branch,
                "limit": request.limit,
            }
        )
    if warning is not None:
        payload["warning"] = warning
    policy_warnings = tuple(getattr(request, "format_policy_warnings", ()) or ())
    if policy_warnings:
        payload["warnings"] = [*([warning] if warning is not None else []), *policy_warnings]
    return payload


def _print_resolved_runtime_settings(
    service: str,
    request: NormalizeFormatRequest | NormalizeAllRequest,
) -> None:
    console.print(_runtime_settings_payload(service, request))


def _print_parser_coverage_table(result: ParserCoverageResult) -> None:
    columns = (
        "branch",
        "role",
        "source_format",
        "files_count",
        "parser_active",
        "parser_class",
        "parser_name",
        "action",
    )
    if Table is None:
        lines = ["\t".join(columns)]
        for row in result.matrix:
            lines.append(
                "\t".join(
                    (
                        row.branch,
                        row.role,
                        row.source_format,
                        str(row.files_count),
                        "yes" if row.parser_active else "no",
                        row.parser_class or "",
                        row.parser_name or "",
                        row.action,
                    )
                )
            )
        console.print("\n".join(lines))
        return

    table = Table(title="Stage Two parser coverage")
    for column in columns:
        table.add_column(column)
    for row in result.matrix:
        table.add_row(
            row.branch,
            row.role,
            row.source_format,
            str(row.files_count),
            "yes" if row.parser_active else "no",
            row.parser_class or "",
            row.parser_name or "",
            row.action,
        )
    console.print(table)


def _json_default(value: Any) -> str:
    return str(value)
