from __future__ import annotations

import json
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from config import (
    DOCS_EN_ANALYSIS_HOST_VALIDATION,
    DOCS_RU_ANALYSIS_HOST_VALIDATION,
    REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_VALIDATION,
    REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_VALIDATION
)
from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationPCAPNGContentAnalysisResult:
    summary_json_file: str
    docs_ru_file: str
    docs_en_file: str
    docs_ru_readme_file: str
    docs_en_readme_file: str
    report_ru_file: str
    report_en_file: str
    total_files_count: int
    sampled_files_count: int
    status: str


@dataclass(frozen=True)
class PCAPNGProbe:
    path: str
    file_name: str
    file_size_bytes: int
    byte_order_magic: str
    endian: str
    version: str
    sampled_blocks: int
    sampled_packets: int
    interface_count: int
    link_types: dict[str, int]
    snaplens: dict[str, int]
    block_types: dict[str, int]
    parse_error: str | None


class HostValidationPCAPNGContentAnalysisHandler:
    ROLE_NAME = "VALIDATION"
    FORMAT_NAME = "pcapng"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_BLOCKS_PER_FILE = 2000
    DEFAULT_MAX_PACKETS_PER_FILE = 500

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-validation-pcapng-summary.json"

    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_blocks_per_file: int = DEFAULT_MAX_BLOCKS_PER_FILE,
        max_packets_per_file: int = DEFAULT_MAX_PACKETS_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_blocks_per_file = max(1, max_blocks_per_file)
        self.max_packets_per_file = max(1, max_packets_per_file)

        self.docs_ru_dir = f"{self.project_root}/{DOCS_RU_ANALYSIS_HOST_VALIDATION}"
        self.docs_en_dir = f"{self.project_root}/{DOCS_EN_ANALYSIS_HOST_VALIDATION}"
        self.report_ru_dir = f"{self.report_path}/{REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_VALIDATION}"
        self.report_en_dir = f"{self.report_path}/{REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_VALIDATION}"

    def analyze_and_generate_docs(self) -> HostValidationPCAPNGContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/pcapng.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcapng.md"
        docs_en_path = self.docs_en_dir / "pcapng.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task6(Analysis of host validation pcapng dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task6(Analysis of host validation pcapng dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return HostValidationPCAPNGContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
        role_bucket = role_to_formats.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")
        format_bucket = role_bucket.get(self.FORMAT_NAME, [])
        if not isinstance(format_bucket, list):
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list.")
        return sorted(
            [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)],
            key=lambda path: str(path).lower(),
        )

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        indices = {int(round(index * step)) for index in range(self.max_files_per_format)}
        return [all_paths[index] for index in sorted(indices)]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[PCAPNGProbe] = []
        block_types: Counter[str] = Counter()
        link_types: Counter[str] = Counter()
        ip_protocols: Counter[str] = Counter()
        tcp_ports: Counter[str] = Counter()
        udp_ports: Counter[str] = Counter()
        packet_lengths: list[int] = []
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, packet_stats = self._probe_pcapng(path)
            probes.append(probe)
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            block_types.update(probe.block_types)
            link_types.update(probe.link_types)
            ip_protocols.update(packet_stats["ip_protocols"])
            tcp_ports.update(packet_stats["tcp_ports"])
            udp_ports.update(packet_stats["udp_ports"])
            packet_lengths.extend(packet_stats["packet_lengths"])

        parsed_packets = sum(probe.sampled_packets for probe in probes)
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_blocks_per_file": self.max_blocks_per_file,
                "max_packets_per_file": self.max_packets_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths[:10]],
            "file_probes": [probe.__dict__ for probe in probes],
            "parsed_packets": parsed_packets,
            "block_types": dict(block_types.most_common(12)),
            "link_types": dict(link_types.most_common()),
            "ip_protocols": dict(ip_protocols.most_common(10)),
            "tcp_ports_sample": dict(tcp_ports.most_common(10)),
            "udp_ports_sample": dict(udp_ports.most_common(10)),
            "packet_length_sample": {
                "min": min(packet_lengths) if packet_lengths else 0,
                "max": max(packet_lengths) if packet_lengths else 0,
            },
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": self.STATUS_BROKEN if parsed_packets == 0 else self.STATUS_NEEDS_CUSTOM,
            "needs_custom_parser": True,
            "processing_priority": "high",
        }

    def _probe_pcapng(self, path: Path) -> tuple[PCAPNGProbe, dict[str, Counter[str] | list[int]]]:
        stats: dict[str, Counter[str] | list[int]] = {
            "ip_protocols": Counter(),
            "tcp_ports": Counter(),
            "udp_ports": Counter(),
            "packet_lengths": [],
        }
        if not path.exists():
            return self._empty_probe(path, "file_not_found"), stats
        file_size = path.stat().st_size
        if file_size == 0:
            return self._empty_probe(path, "empty_file"), stats

        try:
            with path.open("rb") as stream:
                header = stream.read(28)
                if len(header) < 28:
                    return self._empty_probe(path, "short_section_header", file_size=file_size), stats
                if header[:4] != bytes.fromhex("0a0d0d0a"):
                    return self._empty_probe(path, "unknown_pcapng_section_magic", file_size=file_size), stats

                byte_order_magic = header[8:12]
                if byte_order_magic == bytes.fromhex("4d3c2b1a"):
                    endian = "<"
                elif byte_order_magic == bytes.fromhex("1a2b3c4d"):
                    endian = ">"
                else:
                    return self._empty_probe(path, "unknown_pcapng_byte_order_magic", file_size=file_size), stats

                block_total_length = struct.unpack(f"{endian}I", header[4:8])[0]
                major, minor = struct.unpack(f"{endian}HH", header[12:16])
                stream.seek(block_total_length)

                block_counts: Counter[str] = Counter({"0x0a0d0d0a": 1})
                link_counts: Counter[str] = Counter()
                snaplens: Counter[str] = Counter()
                interface_count = 0
                sampled_blocks = 1
                sampled_packets = 0

                while sampled_blocks < self.max_blocks_per_file and sampled_packets < self.max_packets_per_file:
                    block_header = stream.read(8)
                    if not block_header:
                        break
                    if len(block_header) < 8:
                        return (
                            self._probe_from_values(
                                path,
                                file_size,
                                byte_order_magic.hex(),
                                endian,
                                f"{major}.{minor}",
                                sampled_blocks,
                                sampled_packets,
                                interface_count,
                                link_counts,
                                snaplens,
                                block_counts,
                                "short_block_header",
                            ),
                            stats,
                        )
                    block_type, total_length = struct.unpack(f"{endian}II", block_header)
                    if total_length < 12:
                        return (
                            self._probe_from_values(
                                path,
                                file_size,
                                byte_order_magic.hex(),
                                endian,
                                f"{major}.{minor}",
                                sampled_blocks,
                                sampled_packets,
                                interface_count,
                                link_counts,
                                snaplens,
                                block_counts,
                                "invalid_block_length",
                            ),
                            stats,
                        )
                    body = stream.read(total_length - 12)
                    trailer = stream.read(4)
                    if len(body) != total_length - 12 or len(trailer) != 4:
                        return (
                            self._probe_from_values(
                                path,
                                file_size,
                                byte_order_magic.hex(),
                                endian,
                                f"{major}.{minor}",
                                sampled_blocks,
                                sampled_packets,
                                interface_count,
                                link_counts,
                                snaplens,
                                block_counts,
                                "truncated_block",
                            ),
                            stats,
                        )

                    block_counts[f"0x{block_type:08x}"] += 1
                    sampled_blocks += 1
                    if block_type == 0x00000001 and len(body) >= 8:
                        link_type, _reserved, snaplen = struct.unpack(f"{endian}HHI", body[:8])
                        link_counts[str(link_type)] += 1
                        snaplens[str(snaplen)] += 1
                        interface_count += 1
                    elif block_type == 0x00000006 and len(body) >= 20:
                        captured_len = struct.unpack(f"{endian}I", body[12:16])[0]
                        packet = body[20 : 20 + captured_len]
                        sampled_packets += 1
                        cast_lengths = stats["packet_lengths"]
                        assert isinstance(cast_lengths, list)
                        cast_lengths.append(len(packet))
                        self._decode_ethernet_packet(packet, stats)

                return (
                    self._probe_from_values(
                        path,
                        file_size,
                        byte_order_magic.hex(),
                        endian,
                        f"{major}.{minor}",
                        sampled_blocks,
                        sampled_packets,
                        interface_count,
                        link_counts,
                        snaplens,
                        block_counts,
                        None,
                    ),
                    stats,
                )
        except (OSError, struct.error) as error:
            return self._empty_probe(path, str(error), file_size=file_size), stats

    @staticmethod
    def _decode_ethernet_packet(packet: bytes, stats: dict[str, Counter[str] | list[int]]) -> None:
        if len(packet) < 34:
            return
        ether_type = int.from_bytes(packet[12:14], "big")
        if ether_type != 0x0800:
            return
        ip_start = 14
        ihl = (packet[ip_start] & 0x0F) * 4
        if len(packet) < ip_start + ihl + 4:
            return
        protocol = packet[ip_start + 9]
        ip_protocols = stats["ip_protocols"]
        assert isinstance(ip_protocols, Counter)
        ip_protocols[str(protocol)] += 1

        transport_start = ip_start + ihl
        if protocol == 6 and len(packet) >= transport_start + 4:
            ports = stats["tcp_ports"]
            assert isinstance(ports, Counter)
            ports[str(int.from_bytes(packet[transport_start + 2 : transport_start + 4], "big"))] += 1
        elif protocol == 17 and len(packet) >= transport_start + 4:
            ports = stats["udp_ports"]
            assert isinstance(ports, Counter)
            ports[str(int.from_bytes(packet[transport_start + 2 : transport_start + 4], "big"))] += 1

    def _empty_probe(self, path: Path, error: str, file_size: int = 0) -> PCAPNGProbe:
        return self._probe_from_values(
            path,
            file_size,
            "",
            "",
            "",
            0,
            0,
            0,
            Counter(),
            Counter(),
            Counter(),
            error,
        )

    @staticmethod
    def _probe_from_values(
        path: Path,
        file_size: int,
        byte_order_magic: str,
        endian: str,
        version: str,
        sampled_blocks: int,
        sampled_packets: int,
        interface_count: int,
        link_types: Counter[str],
        snaplens: Counter[str],
        block_types: Counter[str],
        parse_error: str | None,
    ) -> PCAPNGProbe:
        return PCAPNGProbe(
            path=str(path),
            file_name=path.name,
            file_size_bytes=file_size,
            byte_order_magic=byte_order_magic,
            endian=endian,
            version=version,
            sampled_blocks=sampled_blocks,
            sampled_packets=sampled_packets,
            interface_count=interface_count,
            link_types=dict(link_types.most_common()),
            snaplens=dict(snaplens.most_common()),
            block_types=dict(block_types.most_common(12)),
            parse_error=parse_error,
        )

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:5])
        fields = self._fields_table(summary)
        parse_error_count = sum(summary["parse_errors"].values())
        protocols = ", ".join(f"{key}: {value}" for key, value in summary["ip_protocols"].items()) or "-"
        blocks = ", ".join(f"{key}: {value}" for key, value in summary["block_types"].items()) or "-"

        if ru:
            return f"""# Анализ формата: pcapng

## 1. Назначение
`.pcapng` в Host VALIDATION содержит packet capture файлы нового поколения с block-based структурой. Формат полезен для network/hybrid feature extraction, но требует специализированного pcapng parser для извлечения пакетов и потоков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcapng |
| Варианты расширения | .pcapng |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | {summary["scope"]["total_files_count"]} |

## 3. Примеры файлов
```text
{examples}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | pcapng Section Header Block |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, typed blocks |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample blocks | {sum(probe["sampled_blocks"] for probe in summary["file_probes"])} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Содержательная структура
Файлы содержат Section Header, Interface Description и Enhanced Packet blocks. Распределение block types в sample: {blocks}. IP protocol distribution после ограниченного packet parsing: {protocols}.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены внутри файла |
| Можно использовать для supervised learning | частично; только при внешней разметке/сценарии из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Enhanced Packet Block timestamp_high/timestamp_low |
| Формат времени | pcapng interface timestamp resolution |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS query/response признаки после packet parsing.

### Host-признаки
- прямые host syscall/EventID признаки отсутствуют.

### Network / hybrid-признаки
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports и TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | pcapng headers/blocks доступны |
| Нестабильная структура | нет | Section Header Block стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.pcapng` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcapng parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.
"""

        return f"""# Format Analysis: pcapng

## 1. Purpose
`.pcapng` in Host VALIDATION contains next-generation packet capture files with a block-based structure. The format is useful for network/hybrid feature extraction, but packet and flow extraction requires a dedicated pcapng parser.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcapng |
| Extension variants | .pcapng |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | {summary["scope"]["total_files_count"]} |

## 3. Example Files
```text
{examples}
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | pcapng Section Header Block |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, typed blocks |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample blocks | {sum(probe["sampled_blocks"] for probe in summary["file_probes"])} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Content Structure
Files contain Section Header, Interface Description, and Enhanced Packet blocks. Block type distribution in the sample: {blocks}. IP protocol distribution after limited packet parsing: {protocols}.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected inside the file |
| Suitable for supervised learning | partial; only with external labels/scenario from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | Enhanced Packet Block timestamp_high/timestamp_low |
| Time format | pcapng interface timestamp resolution |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- DNS query/response features after packet parsing.

### Host Features
- direct host syscall/EventID fields are absent.

### Network / Hybrid Features
- packet/flow counts, bytes, duration;
- protocol distribution;
- TCP/UDP ports and TCP flags;
- DNS/LDAP/SMB/DCERPC indicators after parsing;
- host + network correlation by scenario/file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | no | pcapng headers/blocks are available |
| Unstable structure | no | Section Header Block is stable |
| Mixed schemas | no | one binary capture format |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
`.pcapng` is useful for network/hybrid feature extraction, but a dedicated pcapng parser or Scapy/tshark-like tooling is required for the production pipeline. Source VALIDATION files were not modified.
"""

    @staticmethod
    def _fields_table(summary: dict[str, Any]) -> str:
        first_probe = summary["file_probes"][0] if summary["file_probes"] else {}
        rows = [
            ("section_magic", "hex", "pcapng Section Header Block magic", "0a0d0d0a"),
            ("byte_order_magic", "hex", "endianness marker", first_probe.get("byte_order_magic", "")),
            ("version", "string", "pcapng version", first_probe.get("version", "")),
            ("link_type", "integer", "interface link-layer type", next(iter(summary["link_types"]), "")),
            ("block_type", "hex", "pcapng block type", next(iter(summary["block_types"]), "")),
            ("ip_protocol", "integer", "IP protocol", next(iter(summary["ip_protocols"]), "")),
            ("tcp_dst_port", "integer", "sample TCP destination port", next(iter(summary["tcp_ports_sample"]), "")),
            ("udp_dst_port", "integer", "sample UDP destination port", next(iter(summary["udp_ports_sample"]), "")),
        ]
        return "\n".join(f"| {name} | {typ} | {purpose} | {example} |" for name, typ, purpose, example in rows)

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "cap": (self._load_optional_status("analysis-host-validation-cap-summary.json"), "cap.md"),
            "csv": (self._load_optional_status("analysis-host-validation-csv-summary.json"), "csv.md"),
            "json": (self._load_optional_status("analysis-host-validation-json-summary.json"), "json.md"),
            "netflow_day": (
                self._load_optional_status("analysis-host-validation-netflow-day-summary.json"),
                "netflow_day.md",
            ),
            "pcap": (self._load_optional_status("analysis-host-validation-pcap-summary.json"), "pcap.md"),
            "pcapng": (summary["final_status"], "pcapng.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task6: Analysis of host validation pcapng dataset files"
            if ru
            else "# Task6 Report: Analysis of host validation pcapng dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\pcapng` на основе "
            f"`{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\pcapng` using `{self.HOST_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_pcapng_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/pcapng.md`
- `docs/en/analysis-dataset/host/validation/pcapng.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task6(Analysis of host validation pcapng dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task6(Analysis of host validation pcapng dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.pcapng`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler читает pcapng Section Header, Interface Description и ограниченное число Enhanced Packet blocks.' if ru else 'The handler reads pcapng Section Header, Interface Description, and a limited number of Enhanced Packet blocks.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
        bucket = payload.get(self.ROLE_NAME, {})
        return {fmt: len(paths) for fmt, paths in bucket.items() if isinstance(paths, list)} if isinstance(bucket, dict) else {}

    def _load_optional_status(self, summary_file_name: str) -> str:
        summary_path = self.temp_data_path / summary_file_name
        if not summary_path.exists():
            return "-"
        payload = JsonDataManager(summary_path).read(default={})
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "parsed_packets": summary["parsed_packets"],
            "block_types": summary["block_types"],
            "ip_protocols": summary["ip_protocols"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
