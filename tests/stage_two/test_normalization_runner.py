from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from scripts.db.models import DatasetFile
from scripts.stage_two.cli import _parse_normalize_all_args, _parse_normalize_format_args
from scripts.stage_two.normalization.runner import (
    NormalizeAllRequest,
    NormalizeAllRunner,
    NormalizeFormatRequest,
    NormalizeFormatRunner,
)


@dataclass(frozen=True)
class _FakeParser:
    parser_name: str = "host_auth_log_parser"
    parser_class: str = "HostLineLogParser"


@dataclass(frozen=True)
class _FakeResolution:
    parser: _FakeParser | None
    diagnostics: tuple[Any, ...] = ()


@dataclass(frozen=True)
class _FakeArtifact:
    id: int


class _FakeResolver:
    def __init__(self, parser: _FakeParser | None) -> None:
        self.parser = parser

    def resolve_with_diagnostics(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
    ) -> _FakeResolution:
        return _FakeResolution(parser=self.parser)


class _FakeFileRepository:
    def __init__(self, files: list[DatasetFile]) -> None:
        self.files = files
        self.ready_call: dict[str, Any] | None = None
        self.ready_calls: list[dict[str, Any]] = []

    def get_files_ready_for_parsing(
        self,
        *,
        branch: str | None = None,
        role: str | None = None,
        source_format: str | None = None,
        limit: int | None = None,
        source_group: str | None = None,
    ) -> list[DatasetFile]:
        self.ready_call = {
            "branch": branch,
            "role": role,
            "source_format": source_format,
            "limit": limit,
            "source_group": source_group,
        }
        self.ready_calls.append(self.ready_call)
        result = [
            file
            for file in self.files
            if file.status == "READY_FOR_PARSING"
            and file.branch == branch
            and file.role == role
            and file.source_format == source_format
        ]
        return result[:limit] if limit is not None else result

    def mark_file_status(
        self,
        file: DatasetFile,
        status: str,
        *,
        error_message: str | None = None,
    ) -> DatasetFile:
        file.status = status
        file.error_message = error_message
        return file

    def get_ready_file_groups(
        self,
        *,
        branch: str,
        source_group: str | None = None,
    ) -> list[dict[str, Any]]:
        groups: dict[tuple[str, str], int] = {}
        for file in self.files:
            if file.status == "READY_FOR_PARSING" and file.branch == branch:
                key = (file.role, file.source_format)
                groups[key] = groups.get(key, 0) + 1
        return [
            {"role": role, "source_format": source_format, "files_count": files_count}
            for (role, source_format), files_count in sorted(groups.items())
        ]


class _FakeSession:
    def begin_nested(self) -> "_FakeNestedTransaction":
        return _FakeNestedTransaction()


class _FakeNestedTransaction:
    def __enter__(self) -> "_FakeNestedTransaction":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False


class _FakeNormalizationService:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    def normalize_file(self, dataset_file: DatasetFile) -> _FakeArtifact:
        if dataset_file.file_name == "bad.log":
            raise RuntimeError("parse failed")
        dataset_file.status = "PARSED"
        return _FakeArtifact(id=dataset_file.id or 0)


class NormalizeFormatCliTest(unittest.TestCase):
    def test_parse_normalize_format_flags(self) -> None:
        request = _parse_normalize_format_args(
            [
                "--branch",
                "HOST",
                "--role",
                "train",
                "--format",
                "auth.log",
                "--limit",
                "100",
            ]
        )

        self.assertEqual(
            request,
            NormalizeFormatRequest(
                branch="host",
                role="TRAIN",
                source_format="auth.log",
                limit=100,
            ),
        )

    def test_parse_normalize_format_fallback(self) -> None:
        request = _parse_normalize_format_args(["dns:VALIDATION:pcap:50"])

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.role, "VALIDATION")
        self.assertEqual(request.source_format, "pcap")
        self.assertEqual(request.limit, 50)


class NormalizeAllCliTest(unittest.TestCase):
    def test_parse_normalize_all_flags(self) -> None:
        request = _parse_normalize_all_args(["--branch", "HOST", "--limit", "10"])

        self.assertEqual(request, NormalizeAllRequest(branch="host", limit=10))

    def test_parse_normalize_all_fallback(self) -> None:
        request = _parse_normalize_all_args(["dns:1000"])

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.limit, 1000)


class NormalizeFormatRunnerTest(unittest.TestCase):
    def test_normalize_format_filters_ready_files_and_continues_after_error(self) -> None:
        files = [
            _file(1, "good.log", status="READY_FOR_PARSING"),
            _file(2, "bad.log", status="READY_FOR_PARSING"),
            _file(3, "other.log", status="READY_FOR_PARSING", source_format="syslog"),
            _file(4, "done.log", status="PARSED"),
        ]
        repository = _FakeFileRepository(files)
        runner = _runner(repository, parser=_FakeParser())

        result = runner.normalize_format(
            NormalizeFormatRequest(
                branch="host",
                role="TRAIN",
                source_format="auth.log",
                limit=10,
            )
        )

        self.assertEqual(
            repository.ready_call,
            {
                "branch": "host",
                "role": "TRAIN",
                "source_format": "auth.log",
                "limit": 10,
                "source_group": "PATH_FOLDER_DATASETS_FILTER",
            },
        )
        self.assertEqual(result.selected, 2)
        self.assertEqual(result.processed, 2)
        self.assertEqual(result.parsed, 1)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.normalized, 1)
        self.assertEqual(result.status, "PARTIAL_SUCCESS")
        self.assertEqual([files[0].status, files[1].status], ["PARSED", "FAILED"])

    def test_normalize_format_marks_ready_files_unsupported_without_parser(self) -> None:
        files = [
            _file(1, "one.log", status="READY_FOR_PARSING"),
            _file(2, "two.log", status="READY_FOR_PARSING"),
        ]
        repository = _FakeFileRepository(files)
        runner = _runner(repository, parser=None)

        result = runner.normalize_format(
            NormalizeFormatRequest(branch="host", role="TRAIN", source_format="auth.log")
        )

        self.assertEqual(result.status, "UNSUPPORTED_FORMAT")
        self.assertEqual(result.unsupported, 2)
        self.assertEqual(result.normalized, 0)
        self.assertEqual([file.status for file in files], ["UNSUPPORTED_FORMAT", "UNSUPPORTED_FORMAT"])


class NormalizeAllRunnerTest(unittest.TestCase):
    def test_normalize_all_processes_groups_with_overall_limit(self) -> None:
        files = [
            _file(1, "train-auth.log", status="READY_FOR_PARSING", role="TRAIN"),
            _file(2, "train-syslog.log", status="READY_FOR_PARSING", role="TRAIN", source_format="syslog"),
            _file(3, "validation-auth.log", status="READY_FOR_PARSING", role="VALIDATION"),
        ]
        repository = _FakeFileRepository(files)
        runner = _all_runner(repository, parser=_FakeParser())

        result = runner.normalize_all(NormalizeAllRequest(branch="host", limit=2))

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.selected, 2)
        self.assertEqual(result.normalized, 2)
        self.assertEqual(result.groups_count, 2)
        self.assertEqual(
            [(group.role, group.source_format, group.selected) for group in result.groups],
            [("TRAIN", "auth.log", 1), ("TRAIN", "syslog", 1)],
        )
        self.assertEqual(
            repository.ready_calls,
            [
                {
                    "branch": "host",
                    "role": "TRAIN",
                    "source_format": "auth.log",
                    "limit": 1,
                    "source_group": "PATH_FOLDER_DATASETS_FILTER",
                },
                {
                    "branch": "host",
                    "role": "TRAIN",
                    "source_format": "syslog",
                    "limit": 1,
                    "source_group": "PATH_FOLDER_DATASETS_FILTER",
                },
            ],
        )
        self.assertEqual(
            [file.status for file in files],
            ["PARSED", "PARSED", "READY_FOR_PARSING"],
        )

    def test_normalize_all_keeps_going_when_one_group_has_failed_file(self) -> None:
        files = [
            _file(1, "bad.log", status="READY_FOR_PARSING", role="TRAIN"),
            _file(2, "good.log", status="READY_FOR_PARSING", role="VALIDATION"),
        ]
        repository = _FakeFileRepository(files)
        runner = _all_runner(repository, parser=_FakeParser())

        result = runner.normalize_all(NormalizeAllRequest(branch="host"))

        self.assertEqual(result.status, "PARTIAL_SUCCESS")
        self.assertEqual(result.selected, 2)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.normalized, 1)
        self.assertEqual([file.status for file in files], ["FAILED", "PARSED"])


def _runner(
    repository: _FakeFileRepository,
    *,
    parser: _FakeParser | None,
) -> NormalizeFormatRunner:
    session = _FakeSession()
    runner = NormalizeFormatRunner(
        session,  # type: ignore[arg-type]
        service_factories={"host": _FakeNormalizationService},  # type: ignore[dict-item]
    )
    runner.file_repository = repository  # type: ignore[assignment]
    runner.resolver = _FakeResolver(parser)  # type: ignore[assignment]
    return runner


def _all_runner(
    repository: _FakeFileRepository,
    *,
    parser: _FakeParser | None,
) -> NormalizeAllRunner:
    session = _FakeSession()
    runner = NormalizeAllRunner(
        session,  # type: ignore[arg-type]
        service_factories={"host": _FakeNormalizationService},  # type: ignore[dict-item]
    )
    runner.file_repository = repository  # type: ignore[assignment]
    runner.format_runner.file_repository = repository  # type: ignore[assignment]
    runner.format_runner.resolver = _FakeResolver(parser)  # type: ignore[assignment]
    return runner


def _file(
    file_id: int,
    file_name: str,
    *,
    status: str,
    role: str = "TRAIN",
    source_format: str = "auth.log",
) -> DatasetFile:
    return DatasetFile(
        id=file_id,
        dataset_id=1,
        file_path=f"/tmp/{file_name}",
        file_name=file_name,
        source_format=source_format,
        role=role,
        branch="host",
        status=status,
    )


if __name__ == "__main__":
    unittest.main()
