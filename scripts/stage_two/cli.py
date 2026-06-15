"""CLI route handlers for Stage Two data normalization services."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict
from typing import Any

from rich.console import Console

from config import manage_commands
from scripts.db import session_scope
from scripts.db.repositories import DataQualityRepository, DatasetFileRepository
from scripts.stage_two.duckdb import DuckDBAnalyticsService
from scripts.stage_two.ingestion.catalog_ingestion_service import ingest_configured_catalog_roots
from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.parser_registry.seed import seed_stage_two_metadata
from scripts.stage_two.quality import LeakageChecker
from scripts.stage_two.storage.bootstrap import bootstrap_stage_two_storage
from scripts.stage_two.traceability import TraceabilityError, TraceabilityService


console = Console()

PLANNED_STAGE_TWO_COMMANDS: frozenset[str] = frozenset(
    {
        "parser-coverage",
        "mark-ready",
        "normalize-format",
        "normalize-all",
    }
)


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
    results = ingest_configured_catalog_roots()
    console.print(
        {
            "service": "stage-two catalog-ingest",
            "runs": [asdict(result) for result in results],
            "run_count": len(results),
        }
    )


def _seed_parser_registry() -> None:
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


def _normalize_branch(branch: str, args: Sequence[str]) -> None:
    limit = _parse_optional_limit(args)
    service_class = DnsNormalizationService if branch == "dns" else HostNormalizationService

    with session_scope() as session:
        file_repository = DatasetFileRepository(session)
        files = file_repository.get_files_ready_for_parsing(branch=branch, limit=limit)
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


def _json_default(value: Any) -> str:
    return str(value)
