from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from scripts.db.models import DatasetFile
from scripts.stage_two.cli import (
    _parse_normalize_all_args,
    _parse_normalize_format_args,
    _resolve_format_policy_for_request,
    _runtime_settings_payload,
)
from scripts.stage_two.normalization.options import (
    NormalizationOptions,
    batch_size_for_source_format,
    resolve_normalization_options,
)
from scripts.stage_two.normalization.runner import (
    NormalizeAllRequest,
    NormalizeAllRunner,
    NormalizeFormatRequest,
    NormalizeFormatRunner,
)


@dataclass(frozen=True)
class _FakeParser:
    parser_name: str = "host_auth_log_parser"
    parser_version: str = "v1"
    parser_class: str = "HostLineLogParser"
    normalized_schema_version: str = "v1"


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
        file_ids: tuple[int, ...] | None = None,
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
            and (file_ids is None or file.id in file_ids)
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


class _FakePolicyRepository:
    def __init__(self, _session: object) -> None:
        self.files = [
            _file(1, "one.txt", status="READY_FOR_PARSING", source_format="txt", file_size_bytes=1024),
            _file(2, "two.txt", status="READY_FOR_PARSING", source_format="txt", file_size_bytes=2048),
        ]

    def get_files_ready_for_parsing(self, **_: object) -> list[DatasetFile]:
        return self.files


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
                "--workers",
                "4",
                "--batch-size",
                "1000",
                "--max-output-part-rows",
                "2500",
                "--packet-mode",
                "dns-only",
                "--sample-size",
                "50",
                "--resume",
            ]
        )

        self.assertEqual(
            request,
            NormalizeFormatRequest(
                branch="host",
                role="TRAIN",
                source_format="auth.log",
                limit=100,
                workers=4,
                batch_size=1000,
                max_output_part_rows=2500,
                resume=True,
                packet_mode="dns-only",
                sample_size=50,
            ),
        )

    def test_parse_normalize_format_fallback(self) -> None:
        request = _parse_normalize_format_args(["dns:VALIDATION:pcap:50"])

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.role, "VALIDATION")
        self.assertEqual(request.source_format, "pcap")
        self.assertEqual(request.limit, 50)

    def test_parse_normalize_format_resource_profile_with_cli_override(self) -> None:
        request = _parse_normalize_format_args(
            [
                "--branch",
                "host",
                "--role",
                "TEST",
                "--format",
                "txt",
                "--resource-profile",
                "fast",
                "--workers",
                "6",
                "--resume",
            ]
        )

        self.assertEqual(request.resource_profile, "fast")
        self.assertEqual(request.workers, 6)
        self.assertEqual(request.batch_size, 200_000)
        self.assertEqual(request.max_output_part_rows, 500_000)
        self.assertEqual(request.packet_batch_size, 50_000)
        self.assertFalse(request.hash_outputs)
        self.assertTrue(request.resume)

    def test_normalize_format_policy_uses_catalog_facts_without_overriding_cli_workers(self) -> None:
        request = _parse_normalize_format_args(
            [
                "--branch",
                "host",
                "--role",
                "TEST",
                "--format",
                "txt",
                "--workers",
                "6",
            ]
        )

        with patch("scripts.stage_two.cli.DatasetFileRepository", _FakePolicyRepository):
            resolved = _resolve_format_policy_for_request(object(), request)

        self.assertEqual(resolved.format_policy, "line_fast")
        self.assertEqual(resolved.workers, 6)
        self.assertEqual(resolved.batch_size, 250_000)
        self.assertEqual(resolved.max_output_part_rows, 750_000)
        self.assertEqual(resolved.runtime_facts["file_count"], 2)
        self.assertEqual(resolved.runtime_facts["total_size_bytes"], 3072)

    def test_parse_normalize_format_rejects_unknown_resource_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown resource profile"):
            _parse_normalize_format_args(
                [
                    "--branch",
                    "host",
                    "--role",
                    "TRAIN",
                    "--format",
                    "txt",
                    "--resource-profile",
                    "unsafe",
                ]
            )


class NormalizeAllCliTest(unittest.TestCase):
    def test_parse_normalize_all_flags(self) -> None:
        request = _parse_normalize_all_args(
            [
                "--branch",
                "HOST",
                "--limit",
                "10",
                "--workers",
                "2",
                "--batch-size",
                "500",
                "--max-output-part-rows",
                "1000",
                "--packet-mode",
                "sample",
                "--sample-size",
                "25",
                "--resume",
            ]
        )

        self.assertEqual(
            request,
            NormalizeAllRequest(
                branch="host",
                limit=10,
                workers=2,
                batch_size=500,
                max_output_part_rows=1000,
                resume=True,
                packet_mode="sample",
                sample_size=25,
            ),
        )

    def test_parse_normalize_all_fallback(self) -> None:
        request = _parse_normalize_all_args(["dns:1000"])

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.limit, 1000)

    def test_parse_normalize_all_resource_profile(self) -> None:
        request = _parse_normalize_all_args(["--branch", "host", "--resource-profile", "balanced"])

        self.assertEqual(request.resource_profile, "balanced")
        self.assertEqual(request.workers, 8)
        self.assertEqual(request.batch_size, 100_000)
        self.assertEqual(request.max_output_part_rows, 250_000)
        self.assertEqual(request.packet_batch_size, 50_000)

    def test_runtime_settings_payload_warns_for_aggressive_profile(self) -> None:
        request = _parse_normalize_all_args(["--branch", "host", "--resource-profile", "aggressive"])
        payload = _runtime_settings_payload("normalize-all", request)

        self.assertEqual(payload["resource_profile"], "aggressive")
        self.assertIn("warning", payload)


class NormalizationOptionsProfileTest(unittest.TestCase):
    def test_resolve_normalization_options_preserves_default_safe_mode_without_profile(self) -> None:
        options = resolve_normalization_options()

        self.assertEqual(options.workers, 1)
        self.assertEqual(options.batch_size, 50_000)
        self.assertEqual(options.max_output_part_rows, 50_000)
        self.assertEqual(options.packet_batch_size, 50_000)
        self.assertFalse(options.hash_outputs)
        self.assertIsNone(options.resource_profile)

    def test_normalization_options_validates_packet_batch_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "packet_batch_size"):
            NormalizationOptions(packet_batch_size=0)

    def test_packet_formats_use_packet_batch_size(self) -> None:
        options = NormalizationOptions(batch_size=300_000, packet_batch_size=50_000)

        self.assertEqual(batch_size_for_source_format("pcap", options), 50_000)
        self.assertEqual(batch_size_for_source_format("txt", options), 300_000)


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
    file_size_bytes: int = 100,
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
        file_size_bytes=file_size_bytes,
    )


if __name__ == "__main__":
    unittest.main()
