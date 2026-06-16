"""Parser interfaces and shared parser contracts for Stage Two."""

from scripts.stage_two.parsers.base import (
    BaseParser,
    ParserContext,
    ParserCounters,
    ParserResult,
    ParserStatusDecision,
    build_parser_counters,
    calculate_parser_status,
    limit_error_samples,
)
from scripts.stage_two.parsers.common import (
    build_default_label_fields,
    build_normalized_event,
    build_timestamp_fields,
    build_traceability_fields,
    compact_json_value,
    generate_event_uid,
    merge_json_objects,
)
from scripts.stage_two.parsers.bson import HostBsonSandboxParser
from scripts.stage_two.parsers.dns import DnsCsvParser, DnsPcapCsvParser, DnsTxtDomainListParser
from scripts.stage_two.parsers.host import (
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostMetricbeatParser,
    HostNetflowParser,
    HostSyscallTraceParser,
    HostXmlParser,
)
from scripts.stage_two.parsers.input_reader import (
    InputReaderError,
    ReaderMetadata,
    UniversalInputReader,
)
from scripts.stage_two.parsers.packet import DnsPacketCaptureParser, HostPacketCaptureParser, PacketCaptureParser

PARSER_CLASS_EXPORTS = {
    "DnsCsvParser": DnsCsvParser,
    "DnsPacketCaptureParser": DnsPacketCaptureParser,
    "DnsPcapCsvParser": DnsPcapCsvParser,
    "DnsTxtDomainListParser": DnsTxtDomainListParser,
    "HostBsonSandboxParser": HostBsonSandboxParser,
    "HostCsvParser": HostCsvParser,
    "HostJsonLinesParser": HostJsonLinesParser,
    "HostLineLogParser": HostLineLogParser,
    "HostMetricbeatParser": HostMetricbeatParser,
    "HostNetflowParser": HostNetflowParser,
    "HostPacketCaptureParser": HostPacketCaptureParser,
    "HostSyscallTraceParser": HostSyscallTraceParser,
    "HostXmlParser": HostXmlParser,
    "PacketCaptureParser": PacketCaptureParser,
}

__all__ = [
    "BaseParser",
    "DnsCsvParser",
    "DnsPacketCaptureParser",
    "DnsPcapCsvParser",
    "DnsTxtDomainListParser",
    "HostBsonSandboxParser",
    "HostCsvParser",
    "HostJsonLinesParser",
    "HostLineLogParser",
    "HostMetricbeatParser",
    "HostNetflowParser",
    "HostPacketCaptureParser",
    "HostSyscallTraceParser",
    "HostXmlParser",
    "InputReaderError",
    "PARSER_CLASS_EXPORTS",
    "PacketCaptureParser",
    "ParserContext",
    "ParserCounters",
    "ParserResult",
    "ParserStatusDecision",
    "ReaderMetadata",
    "UniversalInputReader",
    "build_default_label_fields",
    "build_normalized_event",
    "build_parser_counters",
    "build_timestamp_fields",
    "build_traceability_fields",
    "calculate_parser_status",
    "compact_json_value",
    "generate_event_uid",
    "limit_error_samples",
    "merge_json_objects",
]
