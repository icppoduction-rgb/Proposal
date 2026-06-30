"""Line-log parsing helpers for Stage Two Host parsers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from config import STAGE_TWO_MAX_RAW_PREVIEW_BYTES
from scripts.stage_two.parsers.json_utils import loads_json_record


RAW_LINE_PREVIEW_CHARS = min(512, STAGE_TWO_MAX_RAW_PREVIEW_BYTES)
SYSLOG_PREFIX_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>[A-Za-z0-9_./@:+-]+)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)
ISO_PREFIX_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>[A-Za-z0-9_./@:+-]+)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)
JOURNAL_MONOTONIC_RE = re.compile(r"^\[(?P<monotonic>\d+(?:\.\d+)?)\]\s*(?P<message>.+)$")
APACHE_ERROR_RE = re.compile(
    r"^\[(?P<timestamp>[A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d{1,2}\s+"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+\d{4})\]\s+"
    r"\[(?P<module>[A-Za-z0-9_]+):(?P<severity>[A-Za-z0-9_]+)\]\s+"
    r"(?:\[pid\s+(?P<pid>\d+)(?::tid\s+(?P<tid>\d+))?\]\s+)?"
    r"(?P<message>.*)$"
)
AUTH_ACCEPT_RE = re.compile(
    r"\bAccepted\s+(?P<method>\w+)\s+for\s+(?P<user>\S+)\s+from\s+(?P<src_ip>[0-9A-Fa-f:.]+)"
)
AUTH_FAILED_RE = re.compile(
    r"\bFailed\s+(?P<method>\w+)\s+for(?:\s+invalid user)?\s+(?P<user>\S+)\s+from\s+(?P<src_ip>[0-9A-Fa-f:.]+)"
)
SESSION_RE = re.compile(r"\bsession\s+(?P<action>opened|closed)\s+for\s+user\s+(?P<user>\S+)")
SUDO_RE = re.compile(r"^(?P<user>\S+)\s*:\s*(?P<details>.*\bCOMMAND=(?P<command>.+))$")
POSTFIX_CLIENT_RE = re.compile(
    r"\b(?P<queue_id>[A-F0-9]{5,}|[A-Za-z0-9]{5,}):\s+client=(?P<client>[^\s\[]+)(?:\[(?P<src_ip>[0-9A-Fa-f:.]+)\])?"
)
POSTFIX_FROM_RE = re.compile(r"\b(?P<queue_id>[A-F0-9]{5,}|[A-Za-z0-9]{5,}):\s+from=<(?P<sender>[^>]*)>")
POSTFIX_TO_RE = re.compile(r"\b(?P<queue_id>[A-F0-9]{5,}|[A-Za-z0-9]{5,}):\s+to=<(?P<recipient>[^>]*)>")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass(frozen=True)
class ParsedLogLine:
    """Parsed representation of one raw Host log line."""

    row: dict[str, Any]
    source_type: str
    json_payload: Any | None = None
    error: str | None = None


def parse_host_log_line(
    line: str,
    *,
    line_number: int,
    source_format: str,
) -> ParsedLogLine:
    """Parse one raw host log line without preserving the full payload."""
    text = line.rstrip("\r\n")
    stripped = text.strip()
    base = _base_line_fields(text, line_number=line_number, source_format=source_format)
    if not stripped:
        return ParsedLogLine(row=base, source_type="blank", error=f"line {line_number}: blank line")
    if _looks_like_bad_line(stripped):
        return ParsedLogLine(row=base, source_type="invalid", error=f"line {line_number}: invalid control-heavy line")

    if stripped[0] == "{" or _looks_like_json_array(stripped):
        try:
            payload = loads_json_record(stripped)
        except ValueError as exc:
            if stripped[0] == "[":
                row = _parse_prefixed_line(stripped, base)
                row = _enrich_log_row(row)
                return ParsedLogLine(row=row, source_type=str(row.get("_log_source_type") or "raw_line"))
            return ParsedLogLine(
                row=base,
                source_type="json_line",
                error=f"json line {line_number}: {exc}",
            )
        base.update({"_log_source_type": "json_line", "event_type": "json_log"})
        return ParsedLogLine(row=base, source_type="json_line", json_payload=payload)

    row = _parse_prefixed_line(stripped, base)
    row = _enrich_log_row(row)
    return ParsedLogLine(row=row, source_type=str(row.get("_log_source_type") or "raw_line"))


def _base_line_fields(line: str, *, line_number: int, source_format: str) -> dict[str, Any]:
    preview = line[:RAW_LINE_PREVIEW_CHARS]
    return {
        "line_number": line_number,
        "event_index": line_number - 1,
        "source_format": source_format,
        "_raw_line_preview": preview,
        "_raw_line_sha256": hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest(),
        "_raw_line_length": len(line),
    }


def _parse_prefixed_line(line: str, base: dict[str, Any]) -> dict[str, Any]:
    apache_error_match = APACHE_ERROR_RE.match(line)
    if apache_error_match:
        row = dict(base)
        parts = apache_error_match.groupdict()
        message = parts.get("message") or ""
        row.update(
            {
                "_log_source_type": "apache_error",
                "partial_timestamp": parts.get("timestamp"),
                "timestamp_parse_status": "apache_error_timestamp",
                "process_name": "apache2",
                "process_id": parts.get("pid"),
                "message": message[:RAW_LINE_PREVIEW_CHARS],
                "raw_event_name": parts.get("module"),
                "event_type": f"apache_{parts.get('severity') or 'error'}",
                "apache_module": parts.get("module"),
                "apache_severity": parts.get("severity"),
                "thread_id": parts.get("tid"),
            }
        )
        return row

    iso_match = ISO_PREFIX_RE.match(line)
    if iso_match:
        row = dict(base)
        parts = iso_match.groupdict()
        message = parts.get("message") or ""
        row.update(
            {
                "_log_source_type": "iso_syslog",
                "timestamp": parts.get("timestamp"),
                "host_name": parts.get("host"),
                "process_name": parts.get("process"),
                "process_id": parts.get("pid"),
                "message": message[:RAW_LINE_PREVIEW_CHARS],
                "raw_event_name": parts.get("process"),
                "event_type": "log_line",
            }
        )
        return row

    syslog_match = SYSLOG_PREFIX_RE.match(line)
    if syslog_match:
        row = dict(base)
        parts = syslog_match.groupdict()
        partial_timestamp = f"{parts.get('month')} {parts.get('day')} {parts.get('time')}"
        message = parts.get("message") or ""
        row.update(
            {
                "_log_source_type": "syslog",
                "partial_timestamp": partial_timestamp,
                "timestamp_parse_status": "partial_missing_year_timezone",
                "host_name": parts.get("host"),
                "process_name": parts.get("process"),
                "process_id": parts.get("pid"),
                "message": message[:RAW_LINE_PREVIEW_CHARS],
                "raw_event_name": parts.get("process"),
                "event_type": "log_line",
            }
        )
        return row

    journal_match = JOURNAL_MONOTONIC_RE.match(line)
    if journal_match:
        row = dict(base)
        row.update(
            {
                "_log_source_type": "journal",
                "journal_monotonic_seconds": journal_match.group("monotonic"),
                "message": journal_match.group("message")[:RAW_LINE_PREVIEW_CHARS],
                "raw_event_name": "journal",
                "event_type": "journal_line",
            }
        )
        return row

    row = dict(base)
    row.update(
        {
            "_log_source_type": "raw_line",
            "message": line[:RAW_LINE_PREVIEW_CHARS],
            "raw_event_name": "raw_line",
            "event_type": "log_line",
        }
    )
    return row


def _enrich_log_row(row: dict[str, Any]) -> dict[str, Any]:
    message = str(row.get("message") or "")
    process_name = str(row.get("process_name") or "")
    lowered_process = process_name.lower()
    for matcher, event_type in (
        (AUTH_ACCEPT_RE, "auth_login_success"),
        (AUTH_FAILED_RE, "auth_login_failure"),
    ):
        match = matcher.search(message)
        if match:
            row.update(
                {
                    "event_type": event_type,
                    "user_name": match.group("user"),
                    "src_ip": match.group("src_ip"),
                    "auth_method": match.group("method"),
                }
            )
            return row

    session_match = SESSION_RE.search(message)
    if session_match:
        action = session_match.group("action")
        row.update(
            {
                "event_type": f"auth_session_{action}",
                "user_name": session_match.group("user"),
            }
        )
        return row

    if lowered_process == "sudo":
        sudo_match = SUDO_RE.match(message)
        if sudo_match:
            row.update(
                {
                    "event_type": "sudo_command",
                    "user_name": sudo_match.group("user"),
                    "command_line": sudo_match.group("command"),
                }
            )
            return row

    if "postfix" in lowered_process or "mail" in str(row.get("source_format") or "").lower():
        _enrich_mail_row(row, message)
        return row

    if "pam_unix" in message:
        row["event_type"] = "auth_pam_event"
    return row


def _enrich_mail_row(row: dict[str, Any], message: str) -> None:
    for matcher, event_type in (
        (POSTFIX_CLIENT_RE, "mail_client"),
        (POSTFIX_FROM_RE, "mail_from"),
        (POSTFIX_TO_RE, "mail_to"),
    ):
        match = matcher.search(message)
        if not match:
            continue
        row["event_type"] = event_type
        row["mail_queue_id"] = match.groupdict().get("queue_id")
        if match.groupdict().get("src_ip"):
            row["src_ip"] = match.group("src_ip")
        if match.groupdict().get("sender"):
            row["user_name"] = match.group("sender")
        if match.groupdict().get("recipient"):
            row["mail_recipient"] = match.group("recipient")
        if match.groupdict().get("client"):
            row["mail_client"] = match.group("client")
        return
    row["event_type"] = "mail_log"


def _looks_like_bad_line(value: str) -> bool:
    if "\x00" in value:
        return True
    control_count = len(CONTROL_CHAR_RE.findall(value))
    return control_count / max(len(value), 1) > 0.1


def _looks_like_json_array(value: str) -> bool:
    if not value.startswith("["):
        return False
    stripped = value.lstrip()
    if stripped in {"[]", "["}:
        return True
    if len(stripped) < 2:
        return False
    return stripped[1] in '{["-0123456789tfn'
