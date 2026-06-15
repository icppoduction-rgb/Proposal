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
from scripts.stage_two.parsers.bson import HostBsonSandboxParser
from scripts.stage_two.parsers.dns import DnsCsvParser, DnsPcapCsvParser, DnsTxtDomainListParser
from scripts.stage_two.parsers.host import (
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostSyscallTraceParser,
)
from scripts.stage_two.parsers.input_reader import (
    InputReaderError,
    ReaderMetadata,
    UniversalInputReader,
)
from scripts.stage_two.parsers.packet import DnsPacketCaptureParser, HostPacketCaptureParser, PacketCaptureParser

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
    "HostPacketCaptureParser",
    "HostSyscallTraceParser",
    "InputReaderError",
    "PacketCaptureParser",
    "ParserContext",
    "ParserCounters",
    "ParserResult",
    "ParserStatusDecision",
    "ReaderMetadata",
    "UniversalInputReader",
    "build_parser_counters",
    "calculate_parser_status",
    "limit_error_samples",
]
