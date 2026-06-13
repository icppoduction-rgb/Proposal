"""CLI route handlers for Stage Two data normalization services."""

from __future__ import annotations

import json
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
from scripts.stage_two.parser_registry.seed import seed_default_parser_registry
from scripts.stage_two.quality import LeakageChecker
from scripts.stage_two.storage.bootstrap import bootstrap_stage_two_storage
from scripts.stage_two.traceability import TraceabilityError, TraceabilityService


console = Console()


def router_stage_two(service: str | None, action: str | None = None) -> None:
    """Route Stage Two CLI service names to implementation functions."""
    routes = {
        "bootstrap-storage": _bootstrap_storage,
        "catalog-ingest": _catalog_ingest,
        "seed-parser-registry": _seed_parser_registry,
        "normalize-dns": lambda: _normalize_branch("dns", action),
        "normalize-host": lambda: _normalize_branch("host", action),
        "run-duckdb-checks": _run_duckdb_checks,
        "run-leakage-checks": _run_leakage_checks,
        "trace-artifact": lambda: _trace_artifact(action),
    }
    handler = routes.get(service or "")
    if handler is None:
        console.print(manage_commands)
        return
    try:
        handler()
    except ValueError as exc:
        console.print(
            {
                "service": f"stage-two {service}",
                "status": "ERROR",
                "error": str(exc),
            }
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
    result = seed_default_parser_registry()
    console.print(
        {
            "service": "stage-two seed-parser-registry",
            "inserted": result.inserted,
            "updated": result.updated,
        }
    )


def _normalize_branch(branch: str, action: str | None) -> None:
    limit = _parse_optional_limit(action)
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


def _trace_artifact(action: str | None) -> None:
    if not action:
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
                service.get_by_model_ready_id(int(action))
                if action.isdecimal()
                else service.get_by_model_ready_path(action)
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


def _parse_optional_limit(action: str | None) -> int | None:
    if action is None:
        return None
    if action.isdecimal():
        return int(action)
    raise ValueError("normalize action argument must be a non-negative integer limit when provided.")


def _json_default(value: Any) -> str:
    return str(value)
