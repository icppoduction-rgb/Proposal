"""Operational CLI smoke for Stage Two parser workflow commands.

The runner exercises the Stage Two CLI route handlers with synthetic catalog
files, temporary Parquet storage, and a single database transaction that is
rolled back before returning.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from scripts.db import create_session_factory, get_engine
from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.ingestion.catalog_ingestion_service import CatalogIngestionService
from scripts.stage_two.normalization.schema_contracts import NormalizedSchemaRegistry
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parser_catalog_smoke import build_catalog_smoke_files
from scripts.stage_two.parser_registry.seed import ParserRegistrySeeder


@dataclass(frozen=True)
class CliCommandSmokeResult:
    """One command exercised by the operational smoke."""

    command: str
    status: str
    detail: str


@dataclass(frozen=True)
class CliOperationalSmokeResult:
    """Serializable result for Stage Two CLI operational smoke."""

    status: str
    raw_root: str
    storage_root: str
    storage_retained: bool
    commands: tuple[CliCommandSmokeResult, ...]
    coverage_reports_created: bool
    mark_ready_dry_run_preserved_status: bool
    mark_ready_apply_updated_allowed_status: bool
    normalize_format_scoped: bool
    normalize_all_host_roles: tuple[str, ...]
    normalize_all_dns_roles: tuple[str, ...]
    old_commands_exercised: bool
    rollback_verified: bool


class CliOperationalSmokeError(RuntimeError):
    """Raised when an operational CLI smoke assertion fails."""


def run_cli_operational_smoke(*, keep_storage: bool = False) -> CliOperationalSmokeResult:
    """Run Stage Two operational command smoke with DB rollback."""
    temp_root = Path(tempfile.mkdtemp(prefix="stage-two-cli-smoke-"))
    try:
        raw_root = temp_root / "raw"
        storage_root = temp_root / "storage"
        run_id = f"cli-smoke-{uuid4().hex[:12]}"
        cases = build_catalog_smoke_files(raw_root, run_id=run_id)
        source_paths = [str((raw_root / case.relative_path).resolve()) for case in cases]
        result = _run_smoke_transaction(
            raw_root=raw_root,
            storage_root=storage_root,
            source_paths=source_paths,
        )
        if keep_storage:
            return result
        return replace(result, storage_retained=False)
    finally:
        if not keep_storage:
            shutil.rmtree(temp_root, ignore_errors=True)


def _run_smoke_transaction(
    *,
    raw_root: Path,
    storage_root: Path,
    source_paths: list[str],
) -> CliOperationalSmokeResult:
    engine = get_engine()
    session_factory = create_session_factory(engine)
    session = session_factory()
    transaction = session.begin()
    writer = ParquetArtifactWriter(storage_root)
    commands: list[CliCommandSmokeResult] = []
    try:
        NormalizedSchemaRegistry(session).register_contract()
        seed_result = ParserRegistrySeeder(session).seed_from_file()
        _check(not seed_result.validation_errors, "parser registry seed has validation errors")
        ingestion = CatalogIngestionService(session).ingest_root(
            raw_root,
            root_kind="STAGE_TWO_CLI_SMOKE",
        )
        _check(ingestion.files_seen == len(source_paths), "catalog ingestion did not see all smoke files")
        files = _files_by_key(session, source_paths)
        _check(len(files) == len(source_paths), "catalog ingestion did not register all smoke files")
        _assert_no_conflicting_cli_rows(session, source_paths)

        with _patched_cli_runtime(session=session, writer=writer):
            commands.extend(
                [
                    _run_command("python manage.py stage-two parser-coverage", "parser-coverage"),
                    _run_command("python manage.py stage-two parser-coverage host", "parser-coverage", "host"),
                    _run_command("python manage.py stage-two parser-coverage dns", "parser-coverage", "dns"),
                ]
            )
            coverage_reports_created = _coverage_reports_exist()

            auth_file = files[("host", "TRAIN", "auth.log")]
            before_dry_run_status = auth_file.status
            commands.append(
                _run_command(
                    "python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run",
                    "mark-ready",
                    None,
                    ["--branch", "host", "--role", "TRAIN", "--format", "auth.log", "--dry-run"],
                )
            )
            session.refresh(auth_file)
            dry_run_preserved = auth_file.status == before_dry_run_status == "REGISTERED"

            commands.append(
                _run_command(
                    "python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply",
                    "mark-ready",
                    None,
                    ["--branch", "host", "--role", "TRAIN", "--format", "auth.log", "--apply"],
                )
            )
            session.refresh(auth_file)
            apply_updated = auth_file.status == "READY_FOR_PARSING"

            commands.append(
                _run_command(
                    "python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 10",
                    "normalize-format",
                    None,
                    ["--branch", "host", "--role", "TRAIN", "--format", "auth.log", "--limit", "10"],
                )
            )
            session.refresh(auth_file)
            normalize_format_scoped = _normalize_format_was_scoped(session, auth_file.id)

            _mark_ready_direct(session, files[("host", "VALIDATION", "netflow_day")])
            _mark_ready_direct(session, files[("host", "TEST", "bson")])
            commands.append(
                _run_command(
                    "python manage.py stage-two normalize-all --branch host --limit 10",
                    "normalize-all",
                    None,
                    ["--branch", "host", "--limit", "10"],
                )
            )
            host_roles = _artifact_roles_for_branch(session, "host", source_paths)

            _mark_ready_direct(session, files[("dns", "TRAIN", "csv")])
            _mark_ready_direct(session, files[("dns", "VALIDATION", "pcap")])
            commands.append(
                _run_command(
                    "python manage.py stage-two normalize-all --branch dns --limit 10",
                    "normalize-all",
                    None,
                    ["--branch", "dns", "--limit", "10"],
                )
            )
            dns_roles = _artifact_roles_for_branch(session, "dns", source_paths)

            commands.append(_run_command("python manage.py stage-two normalize-host 10", "normalize-host", "10"))
            commands.append(_run_command("python manage.py stage-two normalize-dns 10", "normalize-dns", "10"))

        session.flush()
        transaction.rollback()
        rollback_verified = _verify_rollback(session, source_paths)
        _check(coverage_reports_created, "coverage reports were not created")
        _check(dry_run_preserved, "mark-ready dry-run changed file status")
        _check(apply_updated, "mark-ready apply did not update allowed status")
        _check(normalize_format_scoped, "normalize-format did not stay scoped to host TRAIN auth.log")
        _check(set(host_roles) == {"TRAIN", "VALIDATION", "TEST"}, "normalize-all host role coverage mismatch")
        _check(set(dns_roles) == {"TRAIN", "VALIDATION"}, "normalize-all dns role coverage mismatch")
        _check(rollback_verified, "synthetic dataset_files remain after rollback")
        return CliOperationalSmokeResult(
            status="SUCCESS",
            raw_root=str(raw_root),
            storage_root=str(storage_root),
            storage_retained=True,
            commands=tuple(commands),
            coverage_reports_created=coverage_reports_created,
            mark_ready_dry_run_preserved_status=dry_run_preserved,
            mark_ready_apply_updated_allowed_status=apply_updated,
            normalize_format_scoped=normalize_format_scoped,
            normalize_all_host_roles=tuple(sorted(set(host_roles))),
            normalize_all_dns_roles=tuple(sorted(set(dns_roles))),
            old_commands_exercised=True,
            rollback_verified=rollback_verified,
        )
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


@contextmanager
def _patched_cli_runtime(*, session: Any, writer: ParquetArtifactWriter) -> Any:
    import scripts.stage_two.cli as cli_module
    import scripts.stage_two.normalization.dns_service as dns_service
    import scripts.stage_two.normalization.host_service as host_service
    import scripts.stage_two.parser_coverage as parser_coverage

    @contextmanager
    def smoke_session_scope(*args: Any, **kwargs: Any) -> Any:
        yield session

    original_cli_session_scope = cli_module.session_scope
    original_coverage_session_scope = parser_coverage.session_scope
    original_dns_writer = dns_service.ParquetArtifactWriter
    original_host_writer = host_service.ParquetArtifactWriter
    cli_module.session_scope = smoke_session_scope
    parser_coverage.session_scope = smoke_session_scope
    dns_service.ParquetArtifactWriter = lambda: writer  # type: ignore[assignment]
    host_service.ParquetArtifactWriter = lambda: writer  # type: ignore[assignment]
    try:
        yield
    finally:
        cli_module.session_scope = original_cli_session_scope
        parser_coverage.session_scope = original_coverage_session_scope
        dns_service.ParquetArtifactWriter = original_dns_writer
        host_service.ParquetArtifactWriter = original_host_writer


def _run_command(
    command: str,
    service: str,
    action: str | None = None,
    extra_args: list[str] | None = None,
) -> CliCommandSmokeResult:
    from scripts.stage_two.cli import router_stage_two

    router_stage_two(service, action, extra_args=extra_args or [])
    return CliCommandSmokeResult(command=command, status="SUCCESS", detail="route completed")


def _files_by_key(session: Any, source_paths: list[str]) -> dict[tuple[str, str, str], DatasetFile]:
    statement = select(DatasetFile).where(DatasetFile.file_path.in_(source_paths))
    rows = session.execute(statement).scalars().all()
    return {(row.branch, row.role, row.source_format): row for row in rows}


def _mark_ready_direct(session: Any, dataset_file: DatasetFile) -> None:
    DatasetFileRepository(session).mark_file_status(dataset_file, "READY_FOR_PARSING")


def _assert_no_conflicting_cli_rows(session: Any, source_paths: list[str]) -> None:
    auth_conflicts = session.execute(
        select(func.count(DatasetFile.id)).where(
            DatasetFile.branch == "host",
            DatasetFile.role == "TRAIN",
            DatasetFile.source_format == "auth.log",
            DatasetFile.file_path.not_in(source_paths),
        )
    ).scalar_one()
    _check(
        int(auth_conflicts) == 0,
        "existing host:TRAIN:auth.log rows would be selected by the fixed mark-ready CLI command",
    )
    ready_conflicts = session.execute(
        select(func.count(DatasetFile.id)).where(
            DatasetFile.branch.in_(("host", "dns")),
            DatasetFile.status == "READY_FOR_PARSING",
            DatasetFile.file_path.not_in(source_paths),
        )
    ).scalar_one()
    _check(
        int(ready_conflicts) == 0,
        "existing READY_FOR_PARSING host/dns rows would be selected by normalize-all CLI smoke",
    )


def _normalize_format_was_scoped(session: Any, auth_file_id: int) -> bool:
    artifacts = _artifacts_for_file(session, auth_file_id)
    if len(artifacts) != 1:
        return False
    artifact = artifacts[0]
    return (
        artifact.branch == "host"
        and artifact.role == "TRAIN"
        and artifact.source_format == "auth.log"
        and artifact.status == "SUCCESS"
    )


def _artifact_roles_for_branch(session: Any, branch: str, source_paths: list[str]) -> list[str]:
    file_ids = [
        row.id
        for row in session.execute(
            select(DatasetFile).where(
                DatasetFile.file_path.in_(source_paths),
                DatasetFile.branch == branch,
            )
        )
        .scalars()
        .all()
    ]
    if not file_ids:
        return []
    statement = select(NormalizedArtifact.role).where(NormalizedArtifact.file_id.in_(file_ids))
    return [str(role) for role in session.execute(statement).scalars().all()]


def _artifacts_for_file(session: Any, file_id: int) -> list[NormalizedArtifact]:
    statement = select(NormalizedArtifact).where(NormalizedArtifact.file_id == file_id)
    return list(session.execute(statement).scalars().all())


def _coverage_reports_exist() -> bool:
    from config import PATH_DATA_STORAGE

    root = Path(PATH_DATA_STORAGE).expanduser()
    paths = (
        root / "reports/en/stage-two/parser/parser_coverage_matrix.json",
        root / "reports/ru/stage-two/parser/parser_coverage_matrix.json",
        root / "reports/en/stage-two/parser/parser_coverage_matrix.md",
        root / "reports/ru/stage-two/parser/parser_coverage_matrix.md",
    )
    return all(path.exists() for path in paths)


def _verify_rollback(session: Any, source_paths: list[str]) -> bool:
    statement = select(func.count(DatasetFile.id)).where(DatasetFile.file_path.in_(source_paths))
    return int(session.execute(statement).scalar_one()) == 0


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise CliOperationalSmokeError(message)


def main(argv: list[str] | None = None) -> int:
    """Run the operational CLI smoke from the command line."""
    parser = argparse.ArgumentParser(description="Run Stage Two operational CLI smoke.")
    parser.add_argument(
        "--keep-storage",
        action="store_true",
        help="Keep temporary raw/storage files for debugging.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_cli_operational_smoke(keep_storage=args.keep_storage)
    except Exception as exc:
        print(f"stage-two CLI smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
