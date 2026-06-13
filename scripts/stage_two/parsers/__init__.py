"""Parser interfaces and shared parser contracts for Stage Two."""

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.bson import HostBsonSandboxParser
from scripts.stage_two.parsers.dns import DnsCsvParser, DnsPcapCsvParser, DnsTxtDomainListParser
from scripts.stage_two.parsers.host import (
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostSyscallTraceParser,
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
    "PacketCaptureParser",
    "ParserContext",
    "ParserResult",
]
