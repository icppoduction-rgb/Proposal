"""Full catalog rollback smoke for Stage Two parser normalization.

The smoke uses tiny synthetic raw files and the real Stage Two control plane:
parser registry, catalog ingestion, mark-ready, normalize-format, parser runs,
normalized artifacts, and Parquet output. Database changes are kept inside one
transaction and rolled back before the runner returns.
"""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from scripts.db import create_session_factory, get_engine
from scripts.db.models import DatasetFile, NormalizedArtifact, ParserRun
from scripts.stage_two.ingestion.catalog_ingestion_service import CatalogIngestionService
from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.normalization.runner import NormalizeFormatRequest, NormalizeFormatRunner
from scripts.stage_two.normalization.schema_contracts import NormalizedSchemaRegistry
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parser_registry.seed import ParserRegistrySeeder
from scripts.stage_two.status_tools import MarkReadyRequest, MarkReadyService


EXPECTED_CATALOG_SMOKE_CASES: tuple[tuple[str, str, str], ...] = (
    ("host", "TRAIN", "auth.log"),
    ("host", "VALIDATION", "netflow_day"),
    ("host", "TEST", "bson"),
    ("dns", "TRAIN", "csv"),
    ("dns", "VALIDATION", "pcap"),
)


@dataclass(frozen=True)
class CatalogSmokeCase:
    """One synthetic source file used by the catalog rollback smoke."""

    branch: str
    role: str
    source_format: str
    relative_path: str
    content: bytes


@dataclass(frozen=True)
class CatalogSmokeCaseResult:
    """Validation result for one catalog smoke case."""

    branch: str
    role: str
    source_format: str
    file_id: int
    parser_run_id: int
    artifact_id: int
    file_status: str
    parser_run_status: str
    artifact_status: str
    parquet_path: str
    parquet_exists: bool


@dataclass(frozen=True)
class CatalogSmokeResult:
    """Serializable summary for the full catalog rollback smoke."""

    status: str
    raw_root: str
    storage_root: str
    storage_retained: bool
    ingestion_run_id: int
    files_seen: int
    parser_registry_inserted: int
    parser_registry_updated: int
    cases: tuple[CatalogSmokeCaseResult, ...]
    rollback_verified: bool


class CatalogSmokeError(RuntimeError):
    """Raised when the catalog rollback smoke fails a required assertion."""


def run_catalog_rollback_smoke(*, keep_storage: bool = False) -> CatalogSmokeResult:
    """Run the full DB-backed parser catalog smoke and roll back DB changes."""
    temp_root = Path(tempfile.mkdtemp(prefix="stage-two-catalog-smoke-"))
    try:
        raw_root = temp_root / "raw"
        storage_root = temp_root / "storage"
        run_id = f"catalog-smoke-{uuid4().hex[:12]}"
        cases = build_catalog_smoke_files(raw_root, run_id=run_id)
        result = _run_smoke_transaction(
            raw_root=raw_root,
            storage_root=storage_root,
            cases=cases,
        )
        if keep_storage:
            return result
        return replace(result, storage_retained=False)
    finally:
        if not keep_storage:
            shutil.rmtree(temp_root, ignore_errors=True)


def build_catalog_smoke_files(raw_root: Path, *, run_id: str) -> tuple[CatalogSmokeCase, ...]:
    """Create the required synthetic raw files under a scanner-compatible tree."""
    cases = _catalog_smoke_cases(run_id)
    for case in cases:
        path = raw_root / case.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(case.content)
    return cases


def _catalog_smoke_cases(run_id: str) -> tuple[CatalogSmokeCase, ...]:
    dataset_prefix = f"stage-two-{run_id}"
    dns_packet = _ethernet_ipv4_udp_packet(
        src_ip="10.0.0.1",
        dst_ip="8.8.8.8",
        src_port=53000,
        dst_port=53,
        payload=_dns_query("catalog-smoke.example"),
    )
    return (
        CatalogSmokeCase(
            branch="host",
            role="TRAIN",
            source_format="auth.log",
            relative_path=(
                f"host/{dataset_prefix}-host-auth/TRAIN/auth.log/"
                "sample-auth.log"
            ),
            content=(
                b"Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice "
                b"from 10.0.0.5 port 54421 ssh2\n"
            ),
        ),
        CatalogSmokeCase(
            branch="host",
            role="VALIDATION",
            source_format="netflow_day",
            relative_path=(
                f"host/{dataset_prefix}-host-netflow/VALIDATION/netflow_day/"
                "sample-netflow_day"
            ),
            content=b"1,2,Comp1,Comp2,6,Port12345,Port80,10,20,1000,2000\n",
        ),
        CatalogSmokeCase(
            branch="host",
            role="TEST",
            source_format="bson",
            relative_path=f"host/{dataset_prefix}-host-bson/TEST/bson/sample.bson",
            content=_bson_stream(
                {
                    "I": 1001,
                    "name": "CreateFileW",
                    "type": "api",
                    "category": "file",
                    "args": [{"name": "path"}, {"name": "desired_access"}],
                },
                {
                    "I": 1001,
                    "T": 44,
                    "t": 12.5,
                    "h": 7,
                    "pid": 1337,
                    "process_name": "sample.exe",
                    "args": [r"C:\tmp\a.dll", "GENERIC_READ"],
                },
            ),
        ),
        CatalogSmokeCase(
            branch="dns",
            role="TRAIN",
            source_format="csv",
            relative_path=f"dns/{dataset_prefix}-dns-csv/TRAIN/csv/sample.csv",
            content=b"Domain,TTL,custom_col\nexample.org,60,kept\n",
        ),
        CatalogSmokeCase(
            branch="dns",
            role="VALIDATION",
            source_format="pcap",
            relative_path=f"dns/{dataset_prefix}-dns-pcap/VALIDATION/pcap/sample.pcap",
            content=_pcap_file([dns_packet]),
        ),
    )


def _run_smoke_transaction(
    *,
    raw_root: Path,
    storage_root: Path,
    cases: tuple[CatalogSmokeCase, ...],
) -> CatalogSmokeResult:
    engine = get_engine()
    session_factory = create_session_factory(engine)
    session = session_factory()
    transaction = session.begin()
    source_paths = [str((raw_root / case.relative_path).resolve()) for case in cases]
    try:
        schema_version = NormalizedSchemaRegistry(session).register_contract()
        seed_result = ParserRegistrySeeder(session).seed_from_file()
        _check(not seed_result.validation_errors, "parser registry seed has validation errors")
        _check(schema_version.id is not None, "normalized schema was not registered")

        ingestion = CatalogIngestionService(session).ingest_root(
            raw_root,
            root_kind="STAGE_TWO_CATALOG_SMOKE",
        )
        _check(ingestion.files_seen == len(cases), "catalog ingestion did not see all smoke files")
        files = _catalog_files_by_path(session, source_paths)
        _check(len(files) == len(cases), "catalog ingestion did not register all smoke files")

        writer = ParquetArtifactWriter(storage_root)
        format_runner = NormalizeFormatRunner(
            session,
            service_factories={
                "dns": lambda active_session: DnsNormalizationService(
                    active_session,
                    writer=writer,
                ),
                "host": lambda active_session: HostNormalizationService(
                    active_session,
                    writer=writer,
                ),
            },
        )
        mark_ready = MarkReadyService(session)
        by_key = {
            (file.branch, file.role, file.source_format): file
            for file in files.values()
        }

        case_results: list[CatalogSmokeCaseResult] = []
        for case in cases:
            dataset_file = by_key.get((case.branch, case.role, case.source_format))
            _check(dataset_file is not None, f"catalog row missing for {case.branch}:{case.role}:{case.source_format}")
            case_results.append(
                _run_one_case(
                    session=session,
                    storage_root=storage_root,
                    mark_ready=mark_ready,
                    format_runner=format_runner,
                    case=case,
                    dataset_file=dataset_file,
                )
            )

        session.flush()
        transaction.rollback()
        rollback_verified = _verify_rollback(session, source_paths)
        _check(rollback_verified, "synthetic dataset_files remain after rollback")
        return CatalogSmokeResult(
            status="SUCCESS",
            raw_root=str(raw_root),
            storage_root=str(storage_root),
            storage_retained=True,
            ingestion_run_id=ingestion.run_id,
            files_seen=ingestion.files_seen,
            parser_registry_inserted=seed_result.inserted,
            parser_registry_updated=seed_result.updated,
            cases=tuple(case_results),
            rollback_verified=rollback_verified,
        )
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def _catalog_files_by_path(session: Any, source_paths: list[str]) -> dict[str, DatasetFile]:
    statement = select(DatasetFile).where(DatasetFile.file_path.in_(source_paths))
    rows = session.execute(statement).scalars().all()
    return {row.file_path: row for row in rows}


def _run_one_case(
    *,
    session: Any,
    storage_root: Path,
    mark_ready: MarkReadyService,
    format_runner: NormalizeFormatRunner,
    case: CatalogSmokeCase,
    dataset_file: DatasetFile,
) -> CatalogSmokeCaseResult:
    mark_result = mark_ready.mark_ready(
        MarkReadyRequest(
            branch=case.branch,
            role=case.role,
            source_format=case.source_format,
            apply_changes=True,
            file_ids=(dataset_file.id,),
        )
    )
    _check(mark_result.selected == 1, f"mark-ready selected {mark_result.selected} files for {case.source_format}")
    _check(mark_result.updated == 1, f"mark-ready did not update {case.source_format}")

    normalize_result = format_runner.normalize_format(
        NormalizeFormatRequest(
            branch=case.branch,
            role=case.role,
            source_format=case.source_format,
            limit=1,
            file_ids=(dataset_file.id,),
        )
    )
    _check(normalize_result.selected == 1, f"normalize-format selected {normalize_result.selected} files")
    _check(normalize_result.normalized == 1, f"normalize-format did not normalize {case.source_format}")
    _check(normalize_result.failed == 0, f"normalize-format failed {case.source_format}")
    _check(normalize_result.unsupported == 0, f"normalize-format unsupported {case.source_format}")

    file_result = normalize_result.files[0]
    _check(file_result.artifact_id is not None, f"artifact id missing for {case.source_format}")
    artifact = session.get(NormalizedArtifact, file_result.artifact_id)
    _check(artifact is not None, f"normalized_artifact row missing for {case.source_format}")
    parser_run = _latest_parser_run(session, dataset_file.id)
    _check(parser_run is not None, f"parser_run row missing for {case.source_format}")
    parquet_path = storage_root / artifact.normalized_path
    _check(parquet_path.exists(), f"Parquet output missing for {case.source_format}: {parquet_path}")
    _check((artifact.row_count or 0) > 0, f"normalized_artifact has no rows for {case.source_format}")

    return CatalogSmokeCaseResult(
        branch=case.branch,
        role=case.role,
        source_format=case.source_format,
        file_id=dataset_file.id,
        parser_run_id=parser_run.id,
        artifact_id=artifact.id,
        file_status=dataset_file.status,
        parser_run_status=parser_run.status,
        artifact_status=artifact.status,
        parquet_path=str(parquet_path),
        parquet_exists=True,
    )


def _latest_parser_run(session: Any, file_id: int) -> ParserRun | None:
    statement = (
        select(ParserRun)
        .where(ParserRun.file_id == file_id)
        .order_by(ParserRun.id.desc())
        .limit(1)
    )
    return session.execute(statement).scalar_one_or_none()


def _verify_rollback(session: Any, source_paths: list[str]) -> bool:
    statement = select(func.count(DatasetFile.id)).where(DatasetFile.file_path.in_(source_paths))
    return int(session.execute(statement).scalar_one()) == 0


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogSmokeError(message)


def _pcap_file(packets: list[bytes]) -> bytes:
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    records = []
    for index, packet in enumerate(packets):
        records.append(struct.pack("<IIII", 1_704_067_200 + index, 123456, len(packet), len(packet)))
        records.append(packet)
    return header + b"".join(records)


def _ethernet_ipv4_udp_packet(
    *,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    payload: bytes,
) -> bytes:
    udp_length = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, 0)
    ethernet = b"\xaa\xbb\xcc\xdd\xee\xff" + b"\x11\x22\x33\x44\x55\x66" + struct.pack("!H", 0x0800)
    transport = udp_header + payload
    ipv4_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        20 + len(transport),
        0,
        0,
        64,
        17,
        0,
        _ipv4_bytes(src_ip),
        _ipv4_bytes(dst_ip),
    )
    return ethernet + ipv4_header + transport


def _ipv4_bytes(value: str) -> bytes:
    return bytes(int(part) for part in value.split("."))


def _dns_query(domain: str) -> bytes:
    question = _dns_name(domain) + struct.pack("!HH", 1, 1)
    return struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + question


def _dns_name(domain: str) -> bytes:
    labels = domain.split(".")
    return b"".join(bytes([len(label)]) + label.encode("ascii") for label in labels) + b"\x00"


def _bson_stream(*documents: dict[str, Any]) -> bytes:
    return b"".join(_encode_bson_document(document) for document in documents)


def _encode_bson_document(document: dict[str, Any]) -> bytes:
    body = b"".join(_encode_bson_element(key, value) for key, value in document.items()) + b"\x00"
    return struct.pack("<i", len(body) + 4) + body


def _encode_bson_element(key: str, value: Any) -> bytes:
    key_bytes = key.encode("utf-8") + b"\x00"
    if value is None:
        return b"\x0A" + key_bytes
    if isinstance(value, bool):
        return b"\x08" + key_bytes + (b"\x01" if value else b"\x00")
    if isinstance(value, int):
        if -(2**31) <= value < 2**31:
            return b"\x10" + key_bytes + struct.pack("<i", value)
        return b"\x12" + key_bytes + struct.pack("<q", value)
    if isinstance(value, float):
        return b"\x01" + key_bytes + struct.pack("<d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8") + b"\x00"
        return b"\x02" + key_bytes + struct.pack("<i", len(encoded)) + encoded
    if isinstance(value, dict):
        return b"\x03" + key_bytes + _encode_bson_document(value)
    if isinstance(value, list):
        return b"\x04" + key_bytes + _encode_bson_document({str(index): item for index, item in enumerate(value)})
    if isinstance(value, bytes):
        return b"\x05" + key_bytes + struct.pack("<i", len(value)) + b"\x00" + value
    raise TypeError(f"unsupported BSON smoke value: {value!r}")


def main(argv: list[str] | None = None) -> int:
    """Run the catalog rollback smoke from the command line."""
    parser = argparse.ArgumentParser(description="Run Stage Two full catalog rollback smoke.")
    parser.add_argument(
        "--keep-storage",
        action="store_true",
        help="Keep temporary raw/storage files for debugging.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_catalog_rollback_smoke(keep_storage=args.keep_storage)
    except Exception as exc:
        print(f"parser catalog smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
