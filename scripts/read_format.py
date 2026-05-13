from __future__ import annotations

import argparse
import base64
import configparser
import csv
import gzip
import hashlib
import html.parser
import io
import json
import logging
import plistlib
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


DEFAULT_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1251", "latin-1")
DEFAULT_BINARY_PREVIEW_BYTES = 64 * 1024


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

    def read(self, path: Path) -> dict[str, Any]:
        """Parses CSV content with delimiter sniffing and large-field support."""
        content, encoding = self.read_text_content(path)
        self._set_max_csv_field_size()

        try:
            dialect = csv.Sniffer().sniff(content[:4096])
        except csv.Error:
            dialect = csv.excel

        try:
            with io.StringIO(content, newline="") as stream:
                reader = csv.DictReader(stream, dialect=dialect)
                rows = [dict(row) for row in reader]
        except csv.Error as error:
            raise FileContentProcessingError(f"Cannot parse CSV file: {path}") from error

        return {
            "type": self.format_name,
            "metadata": self.metadata(path) | {"encoding": encoding, "rows": len(rows), "columns": reader.fieldnames or []},
            "content": rows,
        }

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

    def read(self, path: Path) -> dict[str, Any]:
        """Reads PCAP header fields when the magic number is known."""
        sample = self.read_preview(path)
        result = super().read(path)
        result["type"] = self.format_name
        result["metadata"] = result["metadata"] | self._parse_pcap_metadata(sample)
        return result

    def _parse_pcap_metadata(self, payload: bytes) -> dict[str, Any]:
        """Extracts PCAP version, snaplen and network type from global header."""
        magic = payload[:4]
        metadata: dict[str, Any] = {"magic_hex": magic.hex()}

        if magic in {b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4", b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d"} and len(payload) >= 24:
            byte_order = "<" if magic in {b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"} else ">"
            version_major, version_minor, _thiszone, _sigfigs, snaplen, network = struct.unpack(
                f"{byte_order}HHIIII",
                payload[4:24],
            )
            metadata |= {
                "pcap_type": "pcap",
                "version": f"{version_major}.{version_minor}",
                "snaplen": snaplen,
                "network": network,
            }
        elif magic == b"\x0a\x0d\x0d\x0a":
            metadata["pcap_type"] = "pcapng"

        return metadata


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

    def __init__(self, log_path: str | Path | None = None) -> None:
        """Initializes handler registry and optional file logging."""
        self._handlers: dict[str, BaseFileHandler] = {}
        self._pcap_handler = PcapFileHandler()
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

        if ".pcap." in path.name.lower() and extension in self._handlers:
            return self._pcap_handler

        handler = self._handlers.get(extension)
        if handler is None:
            raise UnsupportedFormatError(f"Unsupported file format '{extension or '<none>'}': {path}")

        return handler

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
            ".csv": CsvFileHandler(),
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
    args = parser.parse_args()

    reader = FileFormatReader(log_path=args.log_path)
    result = reader.read(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()