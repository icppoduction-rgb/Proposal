from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from scripts.db.models import DatasetFile
from scripts.stage_two.cli import _parse_mark_ready_args
from scripts.stage_two.status_tools import MarkReadyRequest, MarkReadyService


@dataclass(frozen=True)
class _FakeParser:
    parser_name: str = "host_auth_log_parser"
    parser_class: str = "HostStructuredLogParser"


@dataclass(frozen=True)
class _FakeResolution:
    parser: _FakeParser | None
    diagnostics: tuple[Any, ...] = ()


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


class _FakeSession:
    def __init__(self) -> None:
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1


class MarkReadyCliTest(unittest.TestCase):
    def test_parse_mark_ready_args_defaults_to_dry_run(self) -> None:
        request = _parse_mark_ready_args(
            ["--branch", "HOST", "--role", "train", "--format", "auth.log"]
        )

        self.assertEqual(
            request,
            MarkReadyRequest(
                branch="host",
                role="TRAIN",
                source_format="auth.log",
                apply_changes=False,
            ),
        )

    def test_parse_mark_ready_args_apply_flag(self) -> None:
        request = _parse_mark_ready_args(
            ["--branch", "host", "--role", "TRAIN", "--format", "auth.log", "--apply"]
        )

        self.assertTrue(request.apply_changes)

    def test_parse_mark_ready_retry_failed_flag(self) -> None:
        request = _parse_mark_ready_args(
            [
                "--branch",
                "dns",
                "--role",
                "TRAIN",
                "--format",
                "csv",
                "--retry-failed",
                "--dry-run",
            ]
        )

        self.assertEqual(request.branch, "dns")
        self.assertEqual(request.role, "TRAIN")
        self.assertEqual(request.source_format, "csv")
        self.assertTrue(request.retry_failed)
        self.assertFalse(request.apply_changes)

    def test_parse_mark_ready_fallback(self) -> None:
        request = _parse_mark_ready_args(["apply:host:TRAIN:auth.log"])

        self.assertEqual(request.branch, "host")
        self.assertEqual(request.role, "TRAIN")
        self.assertEqual(request.source_format, "auth.log")
        self.assertTrue(request.apply_changes)

    def test_parse_mark_ready_rejects_apply_and_dry_run_together(self) -> None:
        with self.assertRaises(ValueError):
            _parse_mark_ready_args(
                [
                    "--branch",
                    "host",
                    "--role",
                    "TRAIN",
                    "--format",
                    "auth.log",
                    "--apply",
                    "--dry-run",
                ]
            )


class MarkReadyServiceTest(unittest.TestCase):
    def test_dry_run_does_not_update_files(self) -> None:
        session = _FakeSession()
        files = [_file("REGISTERED"), _file("FAILED"), _file("EMPTY_FILE")]
        service = _service(session, files, parser=_FakeParser())

        result = service.mark_ready(_request(apply_changes=False))

        self.assertEqual([file.status for file in files], ["REGISTERED", "FAILED", "EMPTY_FILE"])
        self.assertEqual(session.flush_count, 0)
        self.assertEqual(result.selected, 3)
        self.assertEqual(result.eligible, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.empty, 1)
        self.assertEqual(result.skipped_by_status, {"EMPTY_FILE": 1, "FAILED": 1})

    def test_apply_updates_only_allowed_statuses(self) -> None:
        session = _FakeSession()
        files = [
            _file("REGISTERED"),
            _file("CHANGED"),
            _file("DISCOVERED"),
            _file("FAILED"),
            _file("PARSED"),
            _file("PARTIALLY_PARSED"),
            _file("SKIPPED"),
            _file("EMPTY_FILE"),
            _file("UNSUPPORTED_FORMAT"),
            _file("READY_FOR_PARSING"),
        ]
        service = _service(session, files, parser=_FakeParser())

        result = service.mark_ready(_request(apply_changes=True))

        self.assertEqual(
            [file.status for file in files],
            [
                "READY_FOR_PARSING",
                "READY_FOR_PARSING",
                "READY_FOR_PARSING",
                "FAILED",
                "PARSED",
                "PARTIALLY_PARSED",
                "SKIPPED",
                "EMPTY_FILE",
                "UNSUPPORTED_FORMAT",
                "READY_FOR_PARSING",
            ],
        )
        self.assertEqual(session.flush_count, 1)
        self.assertEqual(result.eligible, 3)
        self.assertEqual(result.updated, 3)
        self.assertEqual(result.empty, 1)
        self.assertEqual(
            result.skipped_by_status,
            {
                "EMPTY_FILE": 1,
                "FAILED": 1,
                "PARSED": 1,
                "PARTIALLY_PARSED": 1,
                "READY_FOR_PARSING": 1,
                "SKIPPED": 1,
                "UNSUPPORTED_FORMAT": 1,
            },
        )

    def test_unsupported_parser_does_not_update_allowed_statuses(self) -> None:
        session = _FakeSession()
        files = [_file("REGISTERED"), _file("FAILED")]
        service = _service(session, files, parser=None)

        result = service.mark_ready(_request(apply_changes=True))

        self.assertEqual([file.status for file in files], ["REGISTERED", "FAILED"])
        self.assertEqual(session.flush_count, 0)
        self.assertEqual(result.status, "UNSUPPORTED_FORMAT")
        self.assertEqual(result.unsupported, 2)
        self.assertEqual(result.eligible, 0)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped_by_status, {"FAILED": 1})

    def test_retry_failed_updates_only_failed_skipped_and_partial_files(self) -> None:
        session = _FakeSession()
        files = [
            _file("FAILED"),
            _file("SKIPPED"),
            _file("PARTIALLY_PARSED"),
            _file("PARSED"),
            _file("REGISTERED"),
        ]
        service = _service(session, files, parser=_FakeParser())

        result = service.mark_ready(
            MarkReadyRequest(
                branch="host",
                role="TRAIN",
                source_format="auth.log",
                apply_changes=True,
                retry_failed=True,
            )
        )

        self.assertEqual(
            [file.status for file in files],
            [
                "READY_FOR_PARSING",
                "READY_FOR_PARSING",
                "READY_FOR_PARSING",
                "PARSED",
                "REGISTERED",
            ],
        )
        self.assertEqual(result.updated, 3)
        self.assertTrue(result.retry_failed)
        self.assertEqual(session.flush_count, 1)


def _request(*, apply_changes: bool) -> MarkReadyRequest:
    return MarkReadyRequest(
        branch="host",
        role="TRAIN",
        source_format="auth.log",
        apply_changes=apply_changes,
    )


def _file(status: str) -> DatasetFile:
    return DatasetFile(
        dataset_id=1,
        file_path=f"/tmp/{status}.log",
        file_name=f"{status}.log",
        source_format="auth.log",
        role="TRAIN",
        branch="host",
        status=status,
        error_message="previous error",
    )


def _service(
    session: _FakeSession,
    files: list[DatasetFile],
    *,
    parser: _FakeParser | None,
) -> MarkReadyService:
    service = MarkReadyService(session)  # type: ignore[arg-type]
    service.resolver = _FakeResolver(parser)  # type: ignore[assignment]
    service._selected_files = lambda request: list(files)  # type: ignore[method-assign]
    return service


if __name__ == "__main__":
    unittest.main()
