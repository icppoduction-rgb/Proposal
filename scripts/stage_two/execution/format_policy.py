"""Format-specific runtime policy for Stage Two normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.stage_two.normalization.options import NormalizationOptions


LINE_FAST_FORMATS: frozenset[str] = frozenset(
    {
        "log",
        "log-1",
        "log-2",
        "log-3",
        "syslog",
        "syslog.log",
        "syslog-1",
        "syslog-2",
        "syslog-3",
        "syslog-4",
        "messages",
        "messages-1",
        "mainlog",
        "mainlog-1",
        "mainlog-2",
        "mainlog-3",
        "auth.log",
        "mail-info-1",
        "mail-warn-1",
    }
)
WLS_EVENTLOG_FORMATS: frozenset[str] = frozenset({"wls_day"})
SYSCALL_TRACE_FORMATS: frozenset[str] = frozenset({"txt", "sc", "ghc"})
CSV_NETFLOW_FORMATS: frozenset[str] = frozenset({"csv", "pcap.csv", "netflow_day", "netflow_ids"})
JSON_FORMATS: frozenset[str] = frozenset({"json", "json-1"})
BSON_FORMATS: frozenset[str] = frozenset({"bson"})
PACKET_FORMATS: frozenset[str] = frozenset({"cap", "pcap", "pcapng"})
METRIC_LOG_FORMATS: frozenset[str] = frozenset(
    {
        "cpu.log",
        "diskio.log",
        "filesystem.log",
        "fsstat.log",
        "load.log",
        "memory.log",
        "network.log",
        "process.log",
        "process.summary.log",
        "service.log",
        "socket.summary.log",
        "uptime.log",
    }
)
BINARY_FORMATS: frozenset[str] = BSON_FORMATS | PACKET_FORMATS


@dataclass(frozen=True)
class FormatRuntimeFacts:
    """Catalog facts used by format-specific runtime policy."""

    branch: str
    role: str
    source_format: str
    file_count: int = 0
    total_size_bytes: int = 0
    packet_mode: str | None = None

    @property
    def average_file_size(self) -> int:
        """Return average file size in bytes when file_count is known."""
        if self.file_count <= 0:
            return 0
        return self.total_size_bytes // self.file_count

    @property
    def normalized_source_format(self) -> str:
        """Return source_format normalized for policy matching."""
        return self.source_format.strip().lower()

    @property
    def is_binary(self) -> bool:
        """Return True for formats that should avoid line-fast worker settings."""
        return self.normalized_source_format in BINARY_FORMATS

    @property
    def is_line_based(self) -> bool:
        """Return True for source formats treated as line-oriented by policy."""
        return not self.is_binary


@dataclass(frozen=True)
class FormatPolicyDecision:
    """Resolved policy output and operator-facing diagnostics."""

    options: NormalizationOptions
    policy_name: str
    warnings: tuple[str, ...] = ()


def resolve_format_policy(
    base_options: NormalizationOptions,
    facts: FormatRuntimeFacts,
    *,
    explicit_overrides: set[str] | frozenset[str] | None = None,
) -> FormatPolicyDecision:
    """Apply safe source-format defaults without overriding explicit CLI values."""
    overrides = set(explicit_overrides or set())
    policy = _policy_values(facts)
    values = {
        "workers": base_options.workers,
        "batch_size": base_options.batch_size,
        "max_output_part_rows": base_options.max_output_part_rows,
        "packet_batch_size": base_options.packet_batch_size,
        "packet_mode": base_options.packet_mode,
        "engine": base_options.engine,
    }
    for key, value in policy.items():
        if key not in overrides:
            values[key] = value

    warnings = list(_policy_warnings(facts))
    if values["engine"] != "cpu":
        warnings.append(
            "engine is reserved for future acceleration; raw Stage Two normalization still uses CPU parsers"
        )

    options = NormalizationOptions(
        workers=int(values["workers"]),
        batch_size=int(values["batch_size"]),
        max_output_part_rows=int(values["max_output_part_rows"]),
        packet_batch_size=int(values["packet_batch_size"]),
        resume=base_options.resume,
        packet_mode=str(values["packet_mode"]),
        hash_outputs=base_options.hash_outputs,
        sample_size=base_options.sample_size,
        resource_profile=base_options.resource_profile,
        engine=str(values["engine"]),
    )
    return FormatPolicyDecision(
        options=options,
        policy_name=_policy_name(facts),
        warnings=tuple(warnings),
    )


def format_runtime_facts_payload(facts: FormatRuntimeFacts) -> dict[str, Any]:
    """Return serializable facts for CLI resolved-settings output."""
    return {
        "branch": facts.branch,
        "role": facts.role,
        "source_format": facts.source_format,
        "file_count": facts.file_count,
        "total_size_bytes": facts.total_size_bytes,
        "average_file_size": facts.average_file_size,
        "binary": facts.is_binary,
        "line_based": facts.is_line_based,
        "packet_mode": facts.packet_mode,
    }


def _policy_values(facts: FormatRuntimeFacts) -> dict[str, int | str]:
    source_format = facts.normalized_source_format
    if source_format in PACKET_FORMATS:
        return {
            "workers": 3,
            "batch_size": 50_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 100_000,
            "packet_mode": facts.packet_mode or "packet-summary",
            "engine": "cpu",
        }
    if source_format in BSON_FORMATS:
        return {
            "workers": 3,
            "batch_size": 75_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 200_000,
            "engine": "cpu",
        }
    if source_format in JSON_FORMATS:
        return {
            "workers": 8,
            "batch_size": 150_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 500_000,
            "engine": "cpu",
        }
    if source_format in CSV_NETFLOW_FORMATS:
        return {
            "workers": 10,
            "batch_size": 200_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 500_000,
            "engine": "cpu",
        }
    if source_format in WLS_EVENTLOG_FORMATS:
        return {
            "workers": 8,
            "batch_size": 100_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 100_000,
            "engine": "cpu",
        }
    if source_format in SYSCALL_TRACE_FORMATS:
        return {
            "workers": 6,
            "batch_size": 100_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 200_000,
            "engine": "cpu",
        }
    if source_format in LINE_FAST_FORMATS or source_format in METRIC_LOG_FORMATS:
        return {
            "workers": 12,
            "batch_size": 250_000,
            "packet_batch_size": 50_000,
            "max_output_part_rows": 750_000,
            "engine": "cpu",
        }
    return {
        "workers": base_workers_for_unknown(facts),
        "batch_size": 100_000,
        "packet_batch_size": 50_000,
        "max_output_part_rows": 250_000,
        "engine": "cpu",
    }


def base_workers_for_unknown(facts: FormatRuntimeFacts) -> int:
    """Return a conservative worker count for unknown formats."""
    return 4 if facts.total_size_bytes > 0 else 2


def _policy_name(facts: FormatRuntimeFacts) -> str:
    source_format = facts.normalized_source_format
    if source_format in PACKET_FORMATS:
        return "packet_capture"
    if source_format in BSON_FORMATS:
        return "bson"
    if source_format in JSON_FORMATS:
        return "json"
    if source_format in CSV_NETFLOW_FORMATS:
        return "csv_netflow"
    if source_format in WLS_EVENTLOG_FORMATS:
        return "wls_eventlog"
    if source_format in SYSCALL_TRACE_FORMATS:
        return "syscall_trace"
    if source_format in LINE_FAST_FORMATS or source_format in METRIC_LOG_FORMATS:
        return "line_fast"
    return "conservative_unknown"


def _policy_warnings(facts: FormatRuntimeFacts) -> tuple[str, ...]:
    source_format = facts.normalized_source_format
    if source_format in PACKET_FORMATS:
        return ("packet capture parsing is CPU/IO sensitive; policy caps workers and defaults packet_mode=packet-summary",)
    if source_format in BSON_FORMATS:
        return ("BSON parsing is binary and parser-risky; policy caps workers and output part size",)
    if source_format in JSON_FORMATS and facts.average_file_size > 256 * 1024 * 1024:
        return ("large JSON files may include materialized arrays/objects; consider split-large-files only for JSONL-style sources",)
    if source_format in WLS_EVENTLOG_FORMATS and facts.average_file_size > 512 * 1024 * 1024:
        return ("wls_day is JSONL; split into line-aligned chunks around 150 MB with --header no before high-worker normalization",)
    if source_format in SYSCALL_TRACE_FORMATS:
        return (
            "syscall trace parsing is CPU/IO sensitive at high file counts; policy caps workers and output part size",
        )
    if source_format not in LINE_FAST_FORMATS | WLS_EVENTLOG_FORMATS | SYSCALL_TRACE_FORMATS | CSV_NETFLOW_FORMATS | JSON_FORMATS | BSON_FORMATS | PACKET_FORMATS | METRIC_LOG_FORMATS:
        return ("unknown source_format uses conservative runtime policy",)
    return ()
