from __future__ import annotations

import argparse
import base64
import configparser
import csv
import gzip
import hashlib
import html.parser
import io
import ipaddress
import json
import logging
import plistlib
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


DEFAULT_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1251", "latin-1")
DEFAULT_BINARY_PREVIEW_BYTES = 64 * 1024
DEFAULT_DECODED_PREVIEW_BYTES = 256
DEFAULT_PACKET_PAYLOAD_PREVIEW_BYTES = 128
DEFAULT_DECODED_RECORD_PREVIEW_COUNT = 10
DEFAULT_PCAP_RECORD_LIMIT = 10_000
DEFAULT_CSV_ROW_LIMIT = 10_000


PCAP_MAGIC_HEADERS = {
    b"\xd4\xc3\xb2\xa1": ("<", "microsecond"),
    b"\xa1\xb2\xc3\xd4": (">", "microsecond"),
    b"\x4d\x3c\xb2\xa1": ("<", "nanosecond"),
    b"\xa1\xb2\x3c\x4d": (">", "nanosecond"),
}

LINKTYPE_NAMES = {
    1: "Ethernet",
}

ETHERNET_TYPE_NAMES = {
    0x0800: "IPv4",
    0x0806: "ARP",
    0x86DD: "IPv6",
}

IP_PROTOCOL_NAMES = {
    1: "ICMP",
    6: "TCP",
    17: "UDP",
    58: "ICMPv6",
}

PCAPNG_SECTION_HEADER_BLOCK = 0x0A0D0D0A
PCAPNG_INTERFACE_DESCRIPTION_BLOCK = 0x00000001
PCAPNG_SIMPLE_PACKET_BLOCK = 0x00000003
PCAPNG_ENHANCED_PACKET_BLOCK = 0x00000006
PCAPNG_BYTE_ORDER_MAGIC = {
    b"\x4d\x3c\x2b\x1a": "<",
    b"\x1a\x2b\x3c\x4d": ">",
}


TEXT_EXTENSIONS = {
    ".0",
    ".1",
    ".2",
    ".3",
    ".4",
    ".5",
    ".7",
    ".8",
    ".access",
    ".acm",
    ".alias",
    ".allow",
    ".atd",
    ".bak",
    ".bashrc",
    ".blacklist",
    ".cache",
    ".cfg",
    ".client",
    ".cnf",
    ".com",
    ".com_add_aggi_up",
    ".com_add_and_delete_aggi_up",
    ".com_change_ipv4",
    ".com_change_ipv4_post_up",
    ".com_change_ipv4_pre_up",
    ".com_change_ipv6",
    ".com_change_ipv6_post_up",
    ".com_change_ipv6_pre_up",
    ".com_change_method",
    ".com_revert",
    ".com_set_aggi_and_eth0_mtu",
    ".com_set_aggi_slaves",
    ".commit",
    ".commitmeta",
    ".conf",
    ".config",
    ".control",
    ".dat",
    ".default",
    ".defaults",
    ".defs",
    ".delta",
    ".deny",
    ".desktop",
    ".dhclient",
    ".dirmeta",
    ".dirtree",
    ".disabled",
    ".dist",
    ".dpkg-old",
    ".dtd",
    ".example",
    ".ext",
    ".fallback",
    ".filez",
    ".flatpakref",
    ".flatpakrepo",
    ".gen",
    ".ghc",
    ".hcl",
    ".idx",
    ".inc",
    ".info",
    ".ini",
    ".init",
    ".initial_md5sum",
    ".inventory",
    ".iscsi",
    ".j2",
    ".ja",
    ".jfc",
    ".jsonnet",
    ".kmap",
    ".ldif",
    ".list",
    ".load",
    ".local",
    ".lock",
    ".log",
    ".lxc-start",
    ".man",
    ".map",
    ".md",
    ".mime",
    ".mysqld",
    ".net",
    ".netflow_ids",
    ".options",
    ".order",
    ".org",
    ".override",
    ".path",
    ".php",
    ".plymouth",
    ".policy",
    ".prev",
    ".profile",
    ".ps1",
    ".psf",
    ".pub",
    ".py",
    ".rb",
    ".rc",
    ".real",
    ".res",
    ".rst",
    ".rsyslogd",
    ".rules",
    ".sc",
    ".security",
    ".service",
    ".sh",
    ".socket",
    ".spec",
    ".sql",
    ".subr",
    ".svg",
    ".sysctl",
    ".target",
    ".tcpdump",
    ".template",
    ".test_no_changes",
    ".tf",
    ".timer",
    ".tiny",
    ".tmpl",
    ".txt",
    ".types",
    ".ubuntu",
    ".v4",
    ".vga",
    ".xml",
    ".xsd",
    ".yaml",
    ".yml",
}


BINARY_EXTENSIONS = {
    ".bson",
    ".cap",
    ".certs",
    ".crt",
    ".csr",
    ".dmp",
    ".eps",
    ".exe",
    ".gpg",
    ".gpg~",
    ".iso",
    ".journal",
    ".journal~",
    ".key",
    ".keystore",
    ".p12",
    ".pcapng",
    ".pem",
    ".pyc",
    ".sig",
}


TIMESTAMP_PCAP_EXTENSIONS = {
    ".1642084616",
    ".1642084634",
    ".1642084645",
    ".1642084650",
    ".1642084654",
    ".1642171046",
    ".1642254804",
    ".1642260817",
    ".1642334082",
    ".1642339189",
    ".1642421137",
}


class FileFormatError(Exception):
    """Base exception for file format reader errors."""


class UnsupportedFormatError(FileFormatError):
    """Raised when there is no registered handler for the file extension."""


class FileReadError(FileFormatError):
    """Raised when the file cannot be opened or read."""


class FileContentProcessingError(FileFormatError):
    """Raised when file bytes were read but content parsing failed."""


class TextExtractor(html.parser.HTMLParser):
    """Extracts visible text fragments from HTML documents."""

    def __init__(self) -> None:
        """Initializes an empty text accumulator for HTML parser callbacks."""
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collects non-empty text nodes from the HTML parser."""
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    @property
    def text(self) -> str:
        """Returns collected text fragments as a single newline-separated string."""
        return "\n".join(self._parts)


class BaseFileHandler:
    """Base class for all concrete file format handlers."""

    format_name = "base"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads a file and returns normalized content for a concrete format."""
        raise NotImplementedError

    def metadata(self, path: Path) -> dict[str, Any]:
        """Builds common metadata for any readable file."""
        stat = path.stat()
        return {
            "path": str(path),
            "name": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
        }

    def read_bytes(self, path: Path) -> bytes:
        """Reads the whole file as bytes."""
        try:
            with path.open("rb") as file:
                return file.read()
        except OSError as error:
            raise FileReadError(f"Cannot read file: {path}") from error

    def read_preview(self, path: Path, size: int = DEFAULT_BINARY_PREVIEW_BYTES) -> bytes:
        """Reads only the first bytes of a file for metadata and previews."""
        try:
            with path.open("rb") as file:
                return file.read(size)
        except OSError as error:
            raise FileReadError(f"Cannot read file preview: {path}") from error

    def hash_file(self, path: Path) -> str:
        """Calculates SHA-256 without loading the full file into memory."""
        digest = hashlib.sha256()

        try:
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as error:
            raise FileReadError(f"Cannot calculate file hash: {path}") from error

        return digest.hexdigest()

    def read_text_content(self, path: Path) -> tuple[str, str]:
        """Reads text using a small set of expected dataset encodings."""
        payload = self.read_bytes(path)

        for encoding in DEFAULT_TEXT_ENCODINGS:
            try:
                return payload.decode(encoding), encoding
            except UnicodeDecodeError:
                continue

        raise FileContentProcessingError(f"Cannot decode text file with known encodings: {path}")

    def is_probably_text(self, payload: bytes) -> bool:
        """Checks whether a byte sample looks like regular text."""
        if not payload:
            return True

        sample = payload[:8192]
        if sample.count(b"\x00") / len(sample) > 0.05:
            return False

        for encoding in DEFAULT_TEXT_ENCODINGS:
            try:
                text = sample.decode(encoding)
            except UnicodeDecodeError:
                continue

            control_chars = sum(1 for char in text if ord(char) < 32 and char not in "\r\n\t\f\b")
            return control_chars / max(len(text), 1) < 0.10

        return False


class TextFileHandler(BaseFileHandler):
    """Reads plain text-like files."""

    format_name = "text"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads a text file and returns its full content."""
        content, encoding = self.read_text_content(path)
        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding},
            "content": content,
        }


class BinaryFileHandler(BaseFileHandler):
    """Reads binary files as safe base64 previews with metadata."""

    format_name = "binary"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads binary metadata and a bounded base64 preview."""
        preview = self.read_preview(path)
        size = path.stat().st_size
        return {
            "type": self.format_name,
            "metadata": self.metadata(path)
            | {
                "sha256": self.hash_file(path),
                "preview_bytes": len(preview),
                "truncated": len(preview) < size,
            },
            "content_base64": base64.b64encode(preview).decode("ascii"),
        }


class AutoFileHandler(BaseFileHandler):
    """Reads a file as text when possible and as binary otherwise."""

    format_name = "auto"

    def __init__(self) -> None:
        """Initializes reusable text and binary handlers."""
        self._text_handler = TextFileHandler()
        self._binary_handler = BinaryFileHandler()

    def read(self, path: Path) -> dict[str, Any]:
        """Chooses text or binary reading based on a byte sample."""
        sample = self.read_preview(path, size=8192)
        if self.is_probably_text(sample):
            return self._text_handler.read(path)
        return self._binary_handler.read(path)


class CsvFileHandler(TextFileHandler):
    """Reads CSV files into a list of dictionaries."""

    format_name = "csv"

    def __init__(self, row_limit: int | None = DEFAULT_CSV_ROW_LIMIT) -> None:
        """Initializes bounded CSV row extraction settings."""
        self._row_limit = row_limit

    def read(self, path: Path) -> dict[str, Any]:
        """Parses CSV content with streaming reads and large-field support."""
        sample, encoding = self._read_text_sample(path)
        self._set_max_csv_field_size()

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        has_header = self._detect_header(sample)
        rows: list[dict[str, Any]] = []
        rows_seen = 0
        fieldnames: list[str] = []

        try:
            with path.open("r", encoding=encoding, newline="") as stream:
                if has_header:
                    reader = csv.DictReader(stream, dialect=dialect)
                    for row in reader:
                        if self._should_store_csv_row(rows_seen):
                            rows.append(dict(row))
                        rows_seen += 1
                        if not self._should_continue_csv_scan(rows_seen):
                            break
                    fieldnames = list(reader.fieldnames or [])
                else:
                    reader = csv.reader(stream, dialect=dialect)
                    for row in reader:
                        if not fieldnames:
                            fieldnames = [f"column_{index}" for index in range(len(row))]
                        if self._should_store_csv_row(rows_seen):
                            rows.append(self._row_to_dict(row, fieldnames))
                        rows_seen += 1
                        if not self._should_continue_csv_scan(rows_seen):
                            break
        except (OSError, UnicodeDecodeError) as error:
            raise FileReadError(f"Cannot read CSV file: {path}") from error
        except csv.Error as error:
            raise FileContentProcessingError(f"Cannot parse CSV file: {path}") from error

        rows_truncated = self._row_limit is not None and rows_seen > len(rows)
        return {
            "type": self.format_name,
            "metadata": self.metadata(path)
            | {
                "encoding": encoding,
                "has_header": has_header,
                "rows": len(rows),
                "rows_returned": len(rows),
                "rows_scanned": rows_seen,
                "rows_truncated": rows_truncated,
                "row_limit": self._row_limit,
                "columns": fieldnames,
            },
            "content": rows,
        }

    def _read_text_sample(self, path: Path, size: int = 64 * 1024) -> tuple[str, str]:
        """Reads a small text sample to detect CSV encoding and dialect."""
        payload = self.read_preview(path, size=size)

        for encoding in DEFAULT_TEXT_ENCODINGS:
            try:
                return payload.decode(encoding), encoding
            except UnicodeDecodeError:
                continue

        raise FileContentProcessingError(f"Cannot decode CSV sample with known encodings: {path}")

    def _detect_header(self, sample: str) -> bool:
        """Detects whether a CSV sample likely contains a header row."""
        try:
            return csv.Sniffer().has_header(sample)
        except csv.Error:
            return True

    def _should_store_csv_row(self, row_index: int) -> bool:
        """Returns whether a row should be materialized in the result."""
        return self._row_limit is None or row_index < self._row_limit

    def _should_continue_csv_scan(self, rows_seen: int) -> bool:
        """Stops after one row beyond the limit to mark truncation cheaply."""
        return self._row_limit is None or rows_seen <= self._row_limit

    def _row_to_dict(self, row: list[str], fieldnames: list[str]) -> dict[str, Any]:
        """Converts a headerless CSV row to a stable dictionary shape."""
        normalized = {field: row[index] if index < len(row) else None for index, field in enumerate(fieldnames)}
        if len(row) > len(fieldnames):
            normalized["_extra"] = row[len(fieldnames):]
        return normalized

    def _set_max_csv_field_size(self) -> None:
        """Raises CSV field size limit to support large dataset cells."""
        limit = sys.maxsize

        while True:
            try:
                csv.field_size_limit(limit)
                return
            except OverflowError:
                limit //= 10


class JsonFileHandler(TextFileHandler):
    """Reads regular JSON and JSON Lines stored under .json."""

    format_name = "json"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses JSON content and falls back to JSON Lines or raw text."""
        content, encoding = self.read_text_content(path)
        metadata = self.metadata(path) | {"encoding": encoding}

        try:
            return {
                "type": self.format_name,
                "metadata": metadata | {"parsed": True},
                "content": json.loads(content),
            }
        except json.JSONDecodeError:
            pass

        rows = JsonLinesFileHandler.parse_json_lines(content)
        if rows is not None:
            return {
                "type": "jsonl",
                "metadata": metadata | {"parsed": True, "rows": len(rows)},
                "content": rows,
            }

        return {
            "type": self.format_name,
            "metadata": metadata | {"parsed": False},
            "content": content,
        }


class JsonLinesFileHandler(TextFileHandler):
    """Reads JSON Lines and NDJSON files."""

    format_name = "jsonl"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses one JSON document per non-empty line."""
        content, encoding = self.read_text_content(path)
        rows = self.parse_json_lines(content)

        if rows is None:
            raise FileContentProcessingError(f"Invalid JSON Lines file: {path}")

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding, "rows": len(rows)},
            "content": rows,
        }

    @staticmethod
    def parse_json_lines(content: str) -> list[Any] | None:
        """Returns parsed JSON lines or None when at least one line is invalid."""
        rows: list[Any] = []

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError:
                return None

        return rows if rows else None


class XmlFileHandler(TextFileHandler):
    """Reads XML-like files and extracts root tag plus text."""

    format_name = "xml"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses XML when possible and otherwise returns raw text."""
        content, encoding = self.read_text_content(path)

        try:
            root = ElementTree.fromstring(content)
            parsed: dict[str, Any] | None = {
                "root_tag": self.strip_namespace(root.tag),
                "text": " ".join(text.strip() for text in root.itertext() if text.strip()),
            }
        except ElementTree.ParseError:
            parsed = None

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding, "parsed": parsed is not None},
            "content": parsed if parsed is not None else content,
        }

    @staticmethod
    def strip_namespace(tag: str) -> str:
        """Removes an XML namespace prefix from an ElementTree tag."""
        return tag.rsplit("}", maxsplit=1)[-1]


class HtmlFileHandler(TextFileHandler):
    """Reads HTML files and extracts visible text."""

    format_name = "html"

    def read(self, path: Path) -> dict[str, Any]:
        """Returns both extracted text and original HTML."""
        content, encoding = self.read_text_content(path)
        extractor = TextExtractor()
        extractor.feed(content)

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding},
            "content": {"text": extractor.text, "html": content},
        }


class ConfigFileHandler(TextFileHandler):
    """Reads INI-like configuration files."""

    format_name = "config"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses config sections when syntax is compatible with configparser."""
        content, encoding = self.read_text_content(path)
        parser = configparser.ConfigParser(interpolation=None)

        try:
            parser.read_string(content)
            parsed: dict[str, dict[str, str]] | None = {
                section: dict(parser.items(section))
                for section in parser.sections()
            }
        except configparser.Error:
            parsed = None

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding, "parsed": parsed is not None},
            "content": parsed if parsed is not None else content,
        }


class PropertiesFileHandler(TextFileHandler):
    """Reads Java-style .properties files."""

    format_name = "properties"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses key-value pairs separated by '=' or ':'."""
        content, encoding = self.read_text_content(path)
        parsed: dict[str, str] = {}

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "!", ";")):
                continue

            separator_index = self._find_separator(stripped)
            if separator_index < 0:
                continue

            key = stripped[:separator_index].strip()
            value = stripped[separator_index + 1:].strip()
            if key:
                parsed[key] = value

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding, "items": len(parsed)},
            "content": parsed if parsed else content,
        }

    def _find_separator(self, line: str) -> int:
        """Finds the first supported key-value separator in a properties line."""
        indexes = [index for index in (line.find("="), line.find(":")) if index >= 0]
        return min(indexes) if indexes else -1


class GzipFileHandler(BaseFileHandler):
    """Reads gzip-compressed files."""

    format_name = "gzip"

    def read(self, path: Path) -> dict[str, Any]:
        """Decompresses gzip and returns text or binary preview for payload."""
        try:
            with gzip.open(path, "rb") as file:
                payload = file.read()
        except OSError as error:
            raise FileReadError(f"Cannot read gzip file: {path}") from error

        if self.is_probably_text(payload):
            for encoding in DEFAULT_TEXT_ENCODINGS:
                try:
                    content = payload.decode(encoding)
                    return {
                        "type": self.format_name,
                        "metadata": self.metadata(path) | {"encoding": encoding, "decompressed_bytes": len(payload)},
                        "content": content,
                    }
                except UnicodeDecodeError:
                    continue

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"decompressed_bytes": len(payload)},
            "content_base64": base64.b64encode(payload[:DEFAULT_BINARY_PREVIEW_BYTES]).decode("ascii"),
        }


class ZipFileHandler(BaseFileHandler):
    """Base handler for ZIP-based document formats."""

    format_name = "zip"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads archive member names and optional extracted document content."""
        try:
            with zipfile.ZipFile(path) as archive:
                members = archive.namelist()
                content = self.extract_content(archive)
        except (OSError, zipfile.BadZipFile) as error:
            raise FileReadError(f"Cannot read zip-based file: {path}") from error
        except ElementTree.ParseError as error:
            raise FileContentProcessingError(f"Cannot parse zip-based XML content: {path}") from error

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"members": members},
            "content": content if content is not None else {"members": members},
        }

    def extract_content(self, archive: zipfile.ZipFile) -> Any | None:
        """Extracts format-specific content from a ZIP archive."""
        return None


class DocxFileHandler(ZipFileHandler):
    """Reads Microsoft Word .docx files."""

    format_name = "docx"

    def extract_content(self, archive: zipfile.ZipFile) -> dict[str, Any]:
        """Extracts plain text from word/document.xml."""
        root = ElementTree.fromstring(archive.read("word/document.xml"))
        text = "\n".join(node.text for node in root.iter() if XmlFileHandler.strip_namespace(node.tag) == "t" and node.text)
        return {"text": text}


class PptxFileHandler(ZipFileHandler):
    """Reads Microsoft PowerPoint .pptx files."""

    format_name = "pptx"

    def extract_content(self, archive: zipfile.ZipFile) -> dict[str, Any]:
        """Extracts text from all slide XML files."""
        slides: list[dict[str, Any]] = []

        for member in sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")):
            root = ElementTree.fromstring(archive.read(member))
            text = "\n".join(node.text for node in root.iter() if XmlFileHandler.strip_namespace(node.tag) == "t" and node.text)
            slides.append({"name": member, "text": text})

        return {"slides": slides}


class XlsxFileHandler(ZipFileHandler):
    """Reads Microsoft Excel .xlsx files using OOXML XML parts."""

    format_name = "xlsx"

    def extract_content(self, archive: zipfile.ZipFile) -> dict[str, Any]:
        """Extracts worksheet rows with basic shared-string resolution."""
        shared_strings = self._read_shared_strings(archive)
        sheets: dict[str, list[list[Any]]] = {}

        for member in sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
            root = ElementTree.fromstring(archive.read(member))
            rows: list[list[Any]] = []

            for row in root.iter():
                if XmlFileHandler.strip_namespace(row.tag) != "row":
                    continue

                values: list[Any] = []
                for cell in row:
                    if XmlFileHandler.strip_namespace(cell.tag) == "c":
                        values.append(self._read_cell(cell, shared_strings))
                rows.append(values)

            sheets[member] = rows

        return {"sheets": sheets}

    def _read_shared_strings(self, archive: zipfile.ZipFile) -> list[str]:
        """Reads XLSX shared string table when it exists."""
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []

        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        return [
            "".join(node.itertext())
            for node in root
            if XmlFileHandler.strip_namespace(node.tag) == "si"
        ]

    def _read_cell(self, cell: ElementTree.Element, shared_strings: list[str]) -> Any:
        """Converts one XLSX cell XML node to a Python value."""
        cell_type = cell.attrib.get("t")
        value_node = next((node for node in cell if XmlFileHandler.strip_namespace(node.tag) == "v"), None)

        if value_node is None or value_node.text is None:
            inline_text = "".join(cell.itertext()).strip()
            return inline_text or None

        value = value_node.text
        if cell_type == "s":
            index = int(value)
            return shared_strings[index] if 0 <= index < len(shared_strings) else value

        if cell_type in {"str", "inlineStr"}:
            return value

        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


class OdtFileHandler(ZipFileHandler):
    """Reads OpenDocument Text .odt files."""

    format_name = "odt"

    def extract_content(self, archive: zipfile.ZipFile) -> dict[str, Any]:
        """Extracts plain text from content.xml."""
        root = ElementTree.fromstring(archive.read("content.xml"))
        text = "\n".join(text.strip() for text in root.itertext() if text.strip())
        return {"text": text}


class NpzFileHandler(BaseFileHandler):
    """Reads NumPy .npz container metadata without importing numpy."""

    format_name = "npz"

    def read(self, path: Path) -> dict[str, Any]:
        """Lists .npy entries and their header magic versions."""
        arrays: list[dict[str, Any]] = []

        try:
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if not member.endswith(".npy"):
                        continue
                    with archive.open(member) as file:
                        magic = file.read(6)
                        version = tuple(file.read(2))
                        arrays.append({"name": member, "magic": magic.decode("latin-1"), "version": version})
        except (OSError, zipfile.BadZipFile) as error:
            raise FileReadError(f"Cannot read npz file: {path}") from error

        return {
            "type": self.format_name,
            "metadata": self.metadata(path),
            "content": {"arrays": arrays},
        }


class ImageFileHandler(BinaryFileHandler):
    """Reads image files as binary previews plus dimensions when possible."""

    format_name = "image"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads image metadata and bounded binary preview."""
        sample = self.read_preview(path, size=1024 * 1024)
        result = super().read(path)
        result["type"] = self.format_name
        result["image"] = self._parse_dimensions(sample, path.suffix.lower())
        return result

    def _parse_dimensions(self, payload: bytes, extension: str) -> dict[str, int] | None:
        """Parses PNG or JPEG dimensions from file headers."""
        if extension == ".png" and payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
            width, height = struct.unpack(">II", payload[16:24])
            return {"width": width, "height": height}

        if extension in {".jpg", ".jpeg"} and payload.startswith(b"\xff\xd8"):
            return self._parse_jpeg_dimensions(payload)

        return None

    def _parse_jpeg_dimensions(self, payload: bytes) -> dict[str, int] | None:
        """Finds JPEG Start Of Frame marker and returns image dimensions."""
        offset = 2
        while offset + 9 < len(payload):
            if payload[offset] != 0xFF:
                offset += 1
                continue

            marker = payload[offset + 1]
            length = struct.unpack(">H", payload[offset + 2:offset + 4])[0]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", payload[offset + 5:offset + 9])
                return {"width": width, "height": height}

            offset += 2 + length

        return None


class PdfFileHandler(BinaryFileHandler):
    """Reads PDF files as binary previews plus PDF header metadata."""

    format_name = "pdf"

    def read(self, path: Path) -> dict[str, Any]:
        """Reads PDF header and bounded binary preview."""
        sample = self.read_preview(path, size=256)
        result = super().read(path)
        result["type"] = self.format_name
        result["pdf"] = {
            "header": sample[:32].splitlines()[0].decode("latin-1", errors="replace") if sample else "",
        }
        return result


class PcapFileHandler(BinaryFileHandler):
    """Reads PCAP and PCAPNG files as binary previews plus capture metadata."""

    format_name = "pcap"

    def __init__(self, record_limit: int | None = DEFAULT_PCAP_RECORD_LIMIT) -> None:
        """Initializes packet record extraction settings."""
        self._record_limit = record_limit

    def read(self, path: Path) -> dict[str, Any]:
        """Reads PCAP bytes and extracts packet records without embedding raw binary content."""
        payload = self.read_bytes(path)
        metadata, parser = self._parse_capture_header(payload, path)
        if parser["container"] == "pcapng":
            records, records_total, records_truncated, interfaces = self._parse_pcapng_packet_records(payload, parser)
            metadata |= self._pcapng_interface_metadata(interfaces)
        else:
            records, records_total, records_truncated = self._parse_pcap_packet_records(payload, parser)

        return {
            "type": self.format_name,
            "format": self.format_name,
            "metadata": self.metadata(path)
            | {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_bytes": len(payload),
                "content_base64_included": False,
                "records": records_total,
                "records_total": records_total,
                "records_returned": len(records),
                "records_truncated": records_truncated,
                "record_limit": self._record_limit,
            }
            | metadata,
            "records": records,
            "decoded_content": self._decode_pcap_content(payload, records, records_total),
        }

    def _parse_capture_header(self, payload: bytes, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        """Extracts global capture metadata for classic PCAP or PCAPNG."""
        if payload[:4] == b"\x0a\x0d\x0d\x0a":
            return self._parse_pcapng_header(payload, path)
        return self._parse_pcap_header(payload, path)

    def _parse_pcap_header(self, payload: bytes, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        """Extracts PCAP global header and parser settings."""
        if len(payload) < 24:
            raise FileContentProcessingError(f"PCAP file is too small to contain a global header: {path}")

        magic = payload[:4]
        parser_settings = PCAP_MAGIC_HEADERS.get(magic)
        if parser_settings is None:
            raise FileContentProcessingError(f"Unsupported PCAP magic header '{magic.hex()}': {path}")

        byte_order, timestamp_precision = parser_settings
        version_major, version_minor, _thiszone, _sigfigs, snaplen, network = struct.unpack(
            f"{byte_order}HHIIII",
            payload[4:24],
        )

        metadata = {
            "magic_hex": magic.hex(),
            "pcap_type": "pcap",
            "version": f"{version_major}.{version_minor}",
            "snaplen": snaplen,
            "network": network,
            "link_type": LINKTYPE_NAMES.get(network, f"LINKTYPE_{network}"),
            "timestamp_precision": timestamp_precision,
        }
        parser = {
            "container": "pcap",
            "byte_order": byte_order,
            "timestamp_precision": timestamp_precision,
            "network": network,
        }
        return metadata, parser

    def _parse_pcapng_header(self, payload: bytes, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        """Extracts PCAPNG section header and parser settings."""
        if len(payload) < 28:
            raise FileContentProcessingError(f"PCAPNG file is too small to contain a section header: {path}")

        byte_order = PCAPNG_BYTE_ORDER_MAGIC.get(payload[8:12])
        if byte_order is None:
            raise FileContentProcessingError(f"Unsupported PCAPNG byte-order magic '{payload[8:12].hex()}': {path}")

        block_type, block_total_length = struct.unpack(f"{byte_order}II", payload[:8])
        if block_type != PCAPNG_SECTION_HEADER_BLOCK or block_total_length < 28 or block_total_length > len(payload):
            raise FileContentProcessingError(f"Invalid PCAPNG section header block: {path}")

        version_major, version_minor = struct.unpack(f"{byte_order}HH", payload[12:16])
        section_length = struct.unpack(f"{byte_order}q", payload[16:24])[0]
        metadata = {
            "magic_hex": payload[:4].hex(),
            "pcap_type": "pcapng",
            "version": f"{version_major}.{version_minor}",
            "section_length": section_length,
            "timestamp_precision": "microsecond",
        }
        parser = {
            "container": "pcapng",
            "byte_order": byte_order,
            "timestamp_precision": "microsecond",
        }
        return metadata, parser

    def _decode_pcap_content(self, payload: bytes, records: list[dict[str, Any]], records_total: int) -> dict[str, Any]:
        """Returns a human-readable view of the base64-encoded PCAP bytes."""
        preview = payload[:DEFAULT_DECODED_PREVIEW_BYTES]
        return {
            "source_bytes": len(payload),
            "preview_bytes": len(preview),
            "preview_hex": self._format_hex(preview),
            "preview_ascii": self._format_ascii(preview),
            "packets_parsed": records_total,
            "packets_returned": len(records),
            "packets_preview": records[:DEFAULT_DECODED_RECORD_PREVIEW_COUNT],
        }

    def _parse_pcap_packet_records(self, payload: bytes, parser: dict[str, Any]) -> tuple[list[dict[str, Any]], int, bool]:
        """Parses packet records from a classic PCAP payload."""
        byte_order = str(parser["byte_order"])
        offset = 24
        packets: list[dict[str, Any]] = []
        records_total = 0

        while offset + 16 <= len(payload):
            ts_seconds, ts_fraction, captured_length, original_length = struct.unpack(
                f"{byte_order}IIII",
                payload[offset:offset + 16],
            )
            packet_start = offset + 16
            packet_end = min(packet_start + captured_length, len(payload))
            packet_payload = payload[packet_start:packet_end]
            if self._should_store_record(records_total):
                packet_metadata = self._decode_packet_payload(packet_payload, int(parser["network"]))
                packets.append(
                    self._empty_packet_record()
                    | {
                        "index": records_total,
                        "timestamp": self._format_timestamp(
                            ts_seconds,
                            ts_fraction,
                            str(parser["timestamp_precision"]),
                        ),
                        "timestamp_seconds": ts_seconds,
                        "timestamp_fraction": ts_fraction,
                        "packet_length": original_length,
                        "captured_length": captured_length,
                        "original_length": original_length,
                        "available_payload_bytes": len(packet_payload),
                        "truncated": len(packet_payload) < captured_length,
                    }
                    | packet_metadata
                )
            records_total += 1

            if len(packet_payload) < captured_length:
                break

            offset = packet_start + captured_length

        return packets, records_total, records_total > len(packets)

    def _parse_pcapng_packet_records(self, payload: bytes, parser: dict[str, Any]) -> tuple[list[dict[str, Any]], int, bool, list[dict[str, Any]]]:
        """Parses packet records from PCAPNG interface and packet blocks."""
        byte_order = str(parser["byte_order"])
        offset = 0
        packets: list[dict[str, Any]] = []
        interfaces: list[dict[str, Any]] = []
        records_total = 0

        while offset + 12 <= len(payload):
            block_type, block_total_length = struct.unpack(f"{byte_order}II", payload[offset:offset + 8])
            if block_total_length < 12 or offset + block_total_length > len(payload):
                break

            body_start = offset + 8
            body_end = offset + block_total_length - 4
            body = payload[body_start:body_end]

            if block_type == PCAPNG_SECTION_HEADER_BLOCK:
                section_byte_order = PCAPNG_BYTE_ORDER_MAGIC.get(body[:4])
                if section_byte_order is not None:
                    byte_order = section_byte_order
            elif block_type == PCAPNG_INTERFACE_DESCRIPTION_BLOCK:
                interfaces.append(self._parse_pcapng_interface(body, byte_order))
            elif block_type == PCAPNG_ENHANCED_PACKET_BLOCK:
                packet = None
                if self._should_store_record(records_total):
                    packet = self._parse_pcapng_enhanced_packet(body, byte_order, interfaces, records_total)
                if packet is not None:
                    packets.append(packet)
                records_total += 1
            elif block_type == PCAPNG_SIMPLE_PACKET_BLOCK:
                packet = None
                if self._should_store_record(records_total):
                    packet = self._parse_pcapng_simple_packet(body, byte_order, interfaces, records_total)
                if packet is not None:
                    packets.append(packet)
                records_total += 1

            offset += block_total_length

        return packets, records_total, records_total > len(packets), interfaces

    def _should_store_record(self, record_index: int) -> bool:
        """Returns whether a packet record should be materialized in the result."""
        return self._record_limit is None or record_index < self._record_limit

    def _parse_pcapng_interface(self, body: bytes, byte_order: str) -> dict[str, Any]:
        """Parses a PCAPNG Interface Description Block."""
        if len(body) < 8:
            return {"network": 0, "link_type": "LINKTYPE_0", "snaplen": 0, "timestamp_precision": "microsecond"}

        network, _reserved, snaplen = struct.unpack(f"{byte_order}HHI", body[:8])
        options = self._parse_pcapng_options(body[8:], byte_order)
        timestamp_precision = self._parse_pcapng_timestamp_precision(options.get(9))
        return {
            "network": network,
            "link_type": LINKTYPE_NAMES.get(network, f"LINKTYPE_{network}"),
            "snaplen": snaplen,
            "timestamp_precision": timestamp_precision,
        }

    def _parse_pcapng_enhanced_packet(
        self,
        body: bytes,
        byte_order: str,
        interfaces: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:
        """Parses a PCAPNG Enhanced Packet Block."""
        if len(body) < 20:
            return None

        interface_id, timestamp_high, timestamp_low, captured_length, original_length = struct.unpack(
            f"{byte_order}IIIII",
            body[:20],
        )
        packet_start = 20
        packet_end = min(packet_start + captured_length, len(body))
        packet_payload = body[packet_start:packet_end]
        interface = interfaces[interface_id] if interface_id < len(interfaces) else {}
        network = int(interface.get("network", 0))
        timestamp_precision = str(interface.get("timestamp_precision", "microsecond"))
        timestamp_value = (timestamp_high << 32) | timestamp_low

        return (
            self._empty_packet_record()
            | {
                "index": index,
                "interface_id": interface_id,
                "timestamp": self._format_pcapng_timestamp(timestamp_value, timestamp_precision),
                "timestamp_seconds": self._pcapng_timestamp_seconds(timestamp_value, timestamp_precision),
                "timestamp_fraction": self._pcapng_timestamp_fraction(timestamp_value, timestamp_precision),
                "packet_length": original_length,
                "captured_length": captured_length,
                "original_length": original_length,
                "available_payload_bytes": len(packet_payload),
                "truncated": len(packet_payload) < captured_length,
            }
            | self._decode_packet_payload(packet_payload, network)
        )

    def _parse_pcapng_simple_packet(
        self,
        body: bytes,
        byte_order: str,
        interfaces: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:
        """Parses a PCAPNG Simple Packet Block without timestamp metadata."""
        if len(body) < 4:
            return None

        original_length = struct.unpack(f"{byte_order}I", body[:4])[0]
        captured_length = min(original_length, len(body) - 4)
        packet_payload = body[4:4 + captured_length]
        interface = interfaces[0] if interfaces else {}
        network = int(interface.get("network", 0))
        return (
            self._empty_packet_record()
            | {
                "index": index,
                "interface_id": 0,
                "packet_length": original_length,
                "captured_length": len(packet_payload),
                "original_length": original_length,
                "available_payload_bytes": len(packet_payload),
                "truncated": len(packet_payload) < original_length,
            }
            | self._decode_packet_payload(packet_payload, network)
        )

    def _parse_pcapng_options(self, payload: bytes, byte_order: str) -> dict[int, bytes]:
        """Parses PCAPNG block options into raw values keyed by option code."""
        options: dict[int, bytes] = {}
        offset = 0
        while offset + 4 <= len(payload):
            code, length = struct.unpack(f"{byte_order}HH", payload[offset:offset + 4])
            offset += 4
            if code == 0:
                break
            value = payload[offset:offset + length]
            options[code] = value
            offset += length + self._pcapng_padding(length)

        return options

    def _parse_pcapng_timestamp_precision(self, value: bytes | None) -> str:
        """Returns timestamp precision from PCAPNG if_tsresol option."""
        if not value:
            return "microsecond"

        resolution = value[0]
        if resolution & 0x80:
            return f"2^-{resolution & 0x7F}"
        if resolution == 9:
            return "nanosecond"
        if resolution == 6:
            return "microsecond"
        return f"10^-{resolution}"

    def _pcapng_interface_metadata(self, interfaces: list[dict[str, Any]]) -> dict[str, Any]:
        """Builds summary metadata for PCAPNG interfaces."""
        first_interface = interfaces[0] if interfaces else {}
        return {
            "interfaces": len(interfaces),
            "network": first_interface.get("network"),
            "link_type": first_interface.get("link_type"),
            "snaplen": first_interface.get("snaplen"),
        }

    def _pcapng_padding(self, length: int) -> int:
        """Returns PCAPNG 32-bit alignment padding length."""
        return (4 - (length % 4)) % 4

    def _format_pcapng_timestamp(self, value: int, precision: str) -> str:
        """Formats a PCAPNG timestamp as UTC ISO-8601."""
        denominator = self._pcapng_timestamp_denominator(precision)
        seconds = value // denominator
        fraction = value % denominator
        microsecond = fraction * 1_000_000 // denominator
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microsecond).isoformat()

    def _pcapng_timestamp_seconds(self, value: int, precision: str) -> int:
        """Returns whole seconds from a PCAPNG timestamp value."""
        return value // self._pcapng_timestamp_denominator(precision)

    def _pcapng_timestamp_fraction(self, value: int, precision: str) -> int:
        """Returns the raw fractional component for a PCAPNG timestamp value."""
        return value % self._pcapng_timestamp_denominator(precision)

    def _pcapng_timestamp_denominator(self, precision: str) -> int:
        """Returns timestamp units per second for a PCAPNG precision descriptor."""
        if precision == "nanosecond":
            return 1_000_000_000
        if precision == "microsecond":
            return 1_000_000
        if precision.startswith("10^-"):
            return 10 ** int(precision.removeprefix("10^-"))
        if precision.startswith("2^-"):
            return 2 ** int(precision.removeprefix("2^-"))
        return 1_000_000

    def _empty_packet_record(self) -> dict[str, Any]:
        """Builds a stable packet record shape for missing optional metadata."""
        return {
            "timestamp": None,
            "packet_length": None,
            "captured_length": None,
            "link_protocol": None,
            "network_protocol": None,
            "src_ip": None,
            "dst_ip": None,
            "transport_protocol": None,
            "src_port": None,
            "dst_port": None,
            "payload_length": None,
            "has_payload": False,
            "payload_hex_preview": "",
            "payload_ascii_preview": "",
        }

    def _decode_packet_payload(self, payload: bytes, link_type: int) -> dict[str, Any]:
        """Extracts basic L2/L3/L4 metadata without decoding application protocols."""
        if link_type != 1:
            return {
                "link_protocol": LINKTYPE_NAMES.get(link_type, f"LINKTYPE_{link_type}"),
                "payload_length": len(payload),
                "has_payload": bool(payload),
                "payload_hex_preview": self._format_hex(payload[:DEFAULT_PACKET_PAYLOAD_PREVIEW_BYTES]),
                "payload_ascii_preview": self._format_ascii(payload[:DEFAULT_PACKET_PAYLOAD_PREVIEW_BYTES]),
            }

        metadata = self._decode_ethernet_frame(payload)
        preview_payload = metadata.pop("_payload_preview", payload)
        metadata["payload_hex_preview"] = self._format_hex(preview_payload[:DEFAULT_PACKET_PAYLOAD_PREVIEW_BYTES])
        metadata["payload_ascii_preview"] = self._format_ascii(preview_payload[:DEFAULT_PACKET_PAYLOAD_PREVIEW_BYTES])
        return metadata

    def _decode_ethernet_frame(self, payload: bytes) -> dict[str, Any]:
        """Decodes an Ethernet frame and supported network-layer headers."""
        metadata: dict[str, Any] = {
            "link_protocol": "Ethernet",
            "payload_length": max(len(payload) - 14, 0),
            "has_payload": len(payload) > 14,
            "_payload_preview": payload[14:] if len(payload) > 14 else b"",
        }
        if len(payload) < 14:
            return metadata

        ether_type_offset = 12
        ether_type = struct.unpack("!H", payload[ether_type_offset:ether_type_offset + 2])[0]
        frame_offset = 14

        while ether_type in {0x8100, 0x88A8} and len(payload) >= frame_offset + 4:
            ether_type = struct.unpack("!H", payload[frame_offset + 2:frame_offset + 4])[0]
            frame_offset += 4

        metadata["network_protocol"] = ETHERNET_TYPE_NAMES.get(ether_type, f"0x{ether_type:04x}")
        frame_payload = payload[frame_offset:]
        metadata["_payload_preview"] = frame_payload

        if ether_type == 0x0800:
            metadata |= self._decode_ipv4_packet(frame_payload)
        elif ether_type == 0x86DD:
            metadata |= self._decode_ipv6_packet(frame_payload)

        return metadata

    def _decode_ipv4_packet(self, payload: bytes) -> dict[str, Any]:
        """Decodes basic IPv4 and transport header metadata."""
        if len(payload) < 20:
            return {"network_protocol": "IPv4", "payload_length": 0, "has_payload": False}

        version = payload[0] >> 4
        ihl = (payload[0] & 0x0F) * 4
        if version != 4 or ihl < 20 or len(payload) < ihl:
            return {"network_protocol": "IPv4", "payload_length": 0, "has_payload": False}

        total_length = struct.unpack("!H", payload[2:4])[0]
        protocol_number = payload[9]
        packet_length = min(total_length, len(payload)) if total_length else len(payload)
        transport_payload = payload[ihl:packet_length]
        metadata = {
            "network_protocol": "IPv4",
            "src_ip": str(ipaddress.ip_address(payload[12:16])),
            "dst_ip": str(ipaddress.ip_address(payload[16:20])),
            "transport_protocol": IP_PROTOCOL_NAMES.get(protocol_number, str(protocol_number)),
            "payload_length": len(transport_payload),
            "has_payload": bool(transport_payload),
            "_payload_preview": transport_payload,
        }
        return metadata | self._decode_transport_segment(protocol_number, transport_payload)

    def _decode_ipv6_packet(self, payload: bytes) -> dict[str, Any]:
        """Decodes basic IPv6 and direct transport header metadata."""
        if len(payload) < 40 or payload[0] >> 4 != 6:
            return {"network_protocol": "IPv6", "payload_length": 0, "has_payload": False}

        payload_length = struct.unpack("!H", payload[4:6])[0]
        protocol_number = payload[6]
        packet_end = min(40 + payload_length, len(payload))
        transport_payload = payload[40:packet_end]
        metadata = {
            "network_protocol": "IPv6",
            "src_ip": str(ipaddress.ip_address(payload[8:24])),
            "dst_ip": str(ipaddress.ip_address(payload[24:40])),
            "transport_protocol": IP_PROTOCOL_NAMES.get(protocol_number, str(protocol_number)),
            "payload_length": len(transport_payload),
            "has_payload": bool(transport_payload),
            "_payload_preview": transport_payload,
        }
        return metadata | self._decode_transport_segment(protocol_number, transport_payload)

    def _decode_transport_segment(self, protocol_number: int, payload: bytes) -> dict[str, Any]:
        """Decodes basic TCP/UDP/ICMP metadata without L7 parsing."""
        if protocol_number == 17 and len(payload) >= 8:
            udp_length = struct.unpack("!H", payload[4:6])[0]
            payload_end = min(max(udp_length, 8), len(payload))
            app_payload = payload[8:payload_end]
            return {
                "src_port": struct.unpack("!H", payload[0:2])[0],
                "dst_port": struct.unpack("!H", payload[2:4])[0],
                "payload_length": len(app_payload),
                "has_payload": bool(app_payload),
                "_payload_preview": app_payload,
            }

        if protocol_number == 6 and len(payload) >= 20:
            data_offset = (payload[12] >> 4) * 4
            app_payload = payload[data_offset:] if data_offset >= 20 and len(payload) >= data_offset else b""
            return {
                "src_port": struct.unpack("!H", payload[0:2])[0],
                "dst_port": struct.unpack("!H", payload[2:4])[0],
                "payload_length": len(app_payload),
                "has_payload": bool(app_payload),
                "_payload_preview": app_payload,
            }

        if protocol_number in {1, 58} and len(payload) >= 8:
            app_payload = payload[8:]
            return {
                "payload_length": len(app_payload),
                "has_payload": bool(app_payload),
                "_payload_preview": app_payload,
            }

        return {}

    def _format_timestamp(self, seconds: int, fraction: int, precision: str) -> str:
        """Formats a PCAP timestamp as UTC ISO-8601."""
        if precision == "nanosecond":
            microsecond = fraction // 1000
        else:
            microsecond = fraction

        microsecond = max(0, min(microsecond, 999999))
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microsecond).isoformat()

    def _format_hex(self, payload: bytes) -> str:
        """Formats bytes as space-separated hexadecimal for safe display."""
        return payload.hex(" ")

    def _format_ascii(self, payload: bytes) -> str:
        """Formats bytes as printable ASCII, replacing binary bytes with dots."""
        return "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in payload)


class PlistFileHandler(BaseFileHandler):
    """Reads Apple property-list based .webarchive files."""

    format_name = "plist"

    def read(self, path: Path) -> dict[str, Any]:
        """Parses plist content from a binary or XML property list."""
        try:
            with path.open("rb") as file:
                content = plistlib.load(file)
        except (OSError, plistlib.InvalidFileException) as error:
            raise FileContentProcessingError(f"Cannot parse plist file: {path}") from error

        return {
            "type": self.format_name,
            "metadata": self.metadata(path),
            "content": content,
        }


class FileFormatReader:
    """Facade for reading supported file formats through registered handlers."""

    def __init__(
        self,
        log_path: str | Path | None = None,
        pcap_record_limit: int | None = DEFAULT_PCAP_RECORD_LIMIT,
        csv_row_limit: int | None = DEFAULT_CSV_ROW_LIMIT,
    ) -> None:
        """Initializes handler registry and optional file logging."""
        self._handlers: dict[str, BaseFileHandler] = {}
        self._pcap_handler = PcapFileHandler(record_limit=pcap_record_limit)
        self._csv_handler = CsvFileHandler(row_limit=csv_row_limit)
        self._logger = self._build_logger(log_path)
        self._register_default_handlers()

    def __enter__(self) -> FileFormatReader:
        """Returns this reader for use in a with-statement."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Closes logger resources when leaving a with-statement."""
        self.close()

    def read(self, path: str | Path) -> dict[str, Any]:
        """Reads a supported file and returns {'data': normalized_content}."""
        file_path = Path(path)

        try:
            self._validate_file(file_path)
            handler = self._resolve_handler(file_path)
            return {"data": handler.read(file_path)}
        except FileNotFoundError:
            self._logger.exception("File not found: %s", file_path)
            raise
        except UnsupportedFormatError:
            self._logger.exception("Unsupported file format: %s", file_path)
            raise
        except FileReadError:
            self._logger.exception("File reading error: %s", file_path)
            raise
        except FileContentProcessingError:
            self._logger.exception("File content processing error: %s", file_path)
            raise
        except Exception as error:
            self._logger.exception("Unexpected file reading error: %s", file_path)
            raise FileReadError(f"Cannot read file '{file_path}': {error}") from error

    def configure_logging(self, log_path: str | Path | None) -> None:
        """Reconfigures error logging for this reader instance."""
        self._logger = self._build_logger(log_path)

    def close(self) -> None:
        """Closes open logging handlers owned by this reader."""
        self._close_logger_handlers(self._logger)

    def register_handler(self, extension: str, handler: BaseFileHandler) -> None:
        """Registers or replaces a handler for one extension."""
        normalized_extension = self._normalize_extension(extension)
        self._handlers[normalized_extension] = handler

    def supported_extensions(self) -> set[str]:
        """Returns extensions currently supported by this reader."""
        return set(self._handlers)

    def _validate_file(self, path: Path) -> None:
        """Checks that the provided path exists and points to a file."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise FileReadError(f"Path is not a file: {path}")

    def _resolve_handler(self, path: Path) -> BaseFileHandler:
        """Selects a handler by extension with special support for rotated PCAP names."""
        extension = path.suffix.lower()

        if self._is_rotated_pcap_path(path):
            return self._pcap_handler

        handler = self._handlers.get(extension)
        if handler is None:
            raise UnsupportedFormatError(f"Unsupported file format '{extension or '<none>'}': {path}")

        return handler

    def _is_rotated_pcap_path(self, path: Path) -> bool:
        """Returns True for capture files named like traffic.pcap.<timestamp>."""
        return ".pcap." in path.name.lower() and path.suffix.lower() in TIMESTAMP_PCAP_EXTENSIONS

    def _register_default_handlers(self) -> None:
        """Registers all built-in file format handlers."""
        text_handler = TextFileHandler()
        binary_handler = BinaryFileHandler()

        for extension in TEXT_EXTENSIONS:
            self.register_handler(extension, text_handler)

        for extension in BINARY_EXTENSIONS:
            self.register_handler(extension, binary_handler)

        for extension in TIMESTAMP_PCAP_EXTENSIONS:
            self.register_handler(extension, self._pcap_handler)

        specialized_handlers: dict[str, BaseFileHandler] = {
            ".bson": binary_handler,
            ".csv": self._csv_handler,
            ".docx": DocxFileHandler(),
            ".drawio": XmlFileHandler(),
            ".gz": GzipFileHandler(),
            ".html": HtmlFileHandler(),
            ".jpg": ImageFileHandler(),
            ".json": JsonFileHandler(),
            ".npz": NpzFileHandler(),
            ".odt": OdtFileHandler(),
            ".pcap": self._pcap_handler,
            ".pcapng": self._pcap_handler,
            ".pdf": PdfFileHandler(),
            ".png": ImageFileHandler(),
            ".pptx": PptxFileHandler(),
            ".properties": PropertiesFileHandler(),
            ".webarchive": PlistFileHandler(),
            ".xlsx": XlsxFileHandler(),
            ".xml": XmlFileHandler(),
            ".xsd": XmlFileHandler(),
        }

        for extension, handler in specialized_handlers.items():
            self.register_handler(extension, handler)

    def _normalize_extension(self, extension: str) -> str:
        """Normalizes extension spelling before storing it in the registry."""
        value = extension.lower().strip()
        return value if value.startswith(".") else f".{value}"

    def _build_logger(self, log_path: str | Path | None) -> logging.Logger:
        """Creates an instance-specific logger with optional file output."""
        logger = logging.getLogger(f"{__name__}.{id(self)}")
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        self._close_logger_handlers(logger)

        if log_path is None:
            logger.addHandler(logging.NullHandler())
            return logger

        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        return logger

    def _close_logger_handlers(self, logger: logging.Logger) -> None:
        """Removes and closes every handler attached to a logger."""
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def read_file(path: str | Path) -> dict[str, Any]:
    """Backward-compatible helper that reads one file with default reader settings."""
    return FileFormatReader().read(path)


def main() -> None:
    """Runs a small CLI wrapper around FileFormatReader."""
    parser = argparse.ArgumentParser(description="Read a supported file and print normalized JSON.")
    parser.add_argument("path", help="Path to a file")
    parser.add_argument("--log-path", help="Optional path to an error log file")
    parser.add_argument(
        "--pcap-record-limit",
        type=int,
        default=DEFAULT_PCAP_RECORD_LIMIT,
        help=f"Maximum packet records to include for PCAP/PCAPNG files, default: {DEFAULT_PCAP_RECORD_LIMIT}",
    )
    parser.add_argument("--all-pcap-records", action="store_true", help="Include every packet record from PCAP/PCAPNG files")
    parser.add_argument(
        "--csv-row-limit",
        type=int,
        default=DEFAULT_CSV_ROW_LIMIT,
        help=f"Maximum rows to include for CSV files, default: {DEFAULT_CSV_ROW_LIMIT}",
    )
    parser.add_argument("--all-csv-rows", action="store_true", help="Include every row from CSV files")
    args = parser.parse_args()

    pcap_record_limit = None if args.all_pcap_records else args.pcap_record_limit
    csv_row_limit = None if args.all_csv_rows else args.csv_row_limit
    reader = FileFormatReader(log_path=args.log_path, pcap_record_limit=pcap_record_limit, csv_row_limit=csv_row_limit)
    result = reader.read(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
