"""Parser interfaces and shared parser contracts for Stage Two."""

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.dns import DnsCsvParser, DnsPcapCsvParser, DnsTxtDomainListParser
from scripts.stage_two.parsers.host import (
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostSyscallTraceParser,
)

__all__ = [
    "BaseParser",
    "DnsCsvParser",
    "DnsPcapCsvParser",
    "DnsTxtDomainListParser",
    "HostCsvParser",
    "HostJsonLinesParser",
    "HostLineLogParser",
    "HostSyscallTraceParser",
    "ParserContext",
    "ParserResult",
]
