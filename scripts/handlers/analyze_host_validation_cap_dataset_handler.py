from __future__ import annotations

import json
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationCAPContentAnalysisResult:
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
class CAPProbe:
    path: str
    file_name: str
    file_size_bytes: int
    magic: str
    endian: str
    version: str
    snaplen: int
    network: int
    sampled_packets: int
    parse_error: str | None


class HostValidationCAPContentAnalysisHandler:
    ROLE_NAME = "VALIDATION"
    FORMAT_NAME = "cap"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_PACKETS_PER_FILE = 500
    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-validation-cap-summary.json"

    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_packets_per_file: int = DEFAULT_MAX_PACKETS_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_packets_per_file = max(1, max_packets_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "validation"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host" / "validation"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host" / "validation"

    def analyze_and_generate_docs(self) -> HostValidationCAPContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/cap.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "cap.md"
        docs_en_path = self.docs_en_dir / "cap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task1(Analysis of host validation cap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task1(Analysis of host validation cap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return HostValidationCAPContentAnalysisResult(
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
        probes: list[CAPProbe] = []
        link_types: Counter[str] = Counter()
        ip_protocols: Counter[str] = Counter()
        tcp_ports: Counter[str] = Counter()
        udp_ports: Counter[str] = Counter()
        packet_lengths: list[int] = []
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, packet_stats = self._probe_cap(path)
            probes.append(probe)
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            if probe.network:
                link_types[str(probe.network)] += 1
            ip_protocols.update(packet_stats["ip_protocols"])
            tcp_ports.update(packet_stats["tcp_ports"])
            udp_ports.update(packet_stats["udp_ports"])
            packet_lengths.extend(packet_stats["packet_lengths"])

        parsed_packets = sum(probe.sampled_packets for probe in probes)
        final_status = self.STATUS_BROKEN if parsed_packets == 0 else self.STATUS_NEEDS_CUSTOM
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_packets_per_file": self.max_packets_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths[:10]],
            "file_probes": [probe.__dict__ for probe in probes],
            "parsed_packets": parsed_packets,
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
            "final_status": final_status,
            "needs_custom_parser": True,
            "processing_priority": "high",
        }

    def _probe_cap(self, path: Path) -> tuple[CAPProbe, dict[str, Counter[str] | list[int]]]:
        empty_stats: dict[str, Counter[str] | list[int]] = {
            "ip_protocols": Counter(),
            "tcp_ports": Counter(),
            "udp_ports": Counter(),
            "packet_lengths": [],
        }
        if not path.exists():
            return CAPProbe(str(path), path.name, 0, "", "", "", 0, 0, 0, "file_not_found"), empty_stats
        file_size = path.stat().st_size
        if file_size == 0:
            return CAPProbe(str(path), path.name, 0, "", "", "", 0, 0, 0, "empty_file"), empty_stats

        try:
            with path.open("rb") as stream:
                global_header = stream.read(24)
                if len(global_header) < 24:
                    return CAPProbe(str(path), path.name, file_size, global_header.hex(), "", "", 0, 0, 0, "short_global_header"), empty_stats
                magic = global_header[:4]
                endian = "<" if magic in {bytes.fromhex("d4c3b2a1"), bytes.fromhex("4d3cb2a1")} else ">"
                if magic not in {
                    bytes.fromhex("d4c3b2a1"),
                    bytes.fromhex("a1b2c3d4"),
                    bytes.fromhex("4d3cb2a1"),
                    bytes.fromhex("a1b23c4d"),
                }:
                    return CAPProbe(str(path), path.name, file_size, magic.hex(), "", "", 0, 0, 0, "unknown_pcap_magic"), empty_stats

                version_major, version_minor, _thiszone, _sigfigs, snaplen, network = struct.unpack(
                    f"{endian}HHiiii", global_header[4:24]
                )

                sampled_packets = 0
                while sampled_packets < self.max_packets_per_file:
                    packet_header = stream.read(16)
                    if not packet_header:
                        break
                    if len(packet_header) < 16:
                        return (
                            CAPProbe(
                                str(path),
                                path.name,
                                file_size,
                                magic.hex(),
                                endian,
                                f"{version_major}.{version_minor}",
                                snaplen,
                                network,
                                sampled_packets,
                                "short_packet_header",
                            ),
                            empty_stats,
                        )
                    _ts_sec, _ts_usec, incl_len, _orig_len = struct.unpack(f"{endian}IIII", packet_header)
                    packet = stream.read(incl_len)
                    if len(packet) < incl_len:
                        break
                    sampled_packets += 1
                    cast_lengths = empty_stats["packet_lengths"]
                    assert isinstance(cast_lengths, list)
                    cast_lengths.append(incl_len)
                    if network == 1:
                        self._decode_ethernet_packet(packet, empty_stats)

                return (
                    CAPProbe(
                        str(path),
                        path.name,
                        file_size,
                        magic.hex(),
                        endian,
                        f"{version_major}.{version_minor}",
                        snaplen,
                        network,
                        sampled_packets,
                        None,
                    ),
                    empty_stats,
                )
        except OSError as error:
            return CAPProbe(str(path), path.name, file_size, "", "", "", 0, 0, 0, str(error)), empty_stats

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

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._fields_table(summary, language)
        parse_error_count = sum(summary["parse_errors"].values())
        protocols = ", ".join(f"{key}: {value}" for key, value in summary["ip_protocols"].items()) or "-"

        if ru:
            return f"""# Анализ формата: cap

## 1. Назначение
`.cap` в Host VALIDATION содержит classic pcap packet capture файлы с сетевым трафиком attack-сценариев. Формат нужен для network/hybrid feature extraction, но требует специализированного packet parser для полного извлечения признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | cap |
| Варианты расширения | .cap |
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
| Заголовок | pcap global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Содержательная структура
Файлы содержат packet metadata и payload bytes в classic pcap container. В sample обнаружены Ethernet/IPv4 пакеты; IP protocol distribution: {protocols}. Имена файлов указывают на attack scenario и могут использоваться как внешний контекст, но не как встроенное label-поле.

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
| Название поля | packet header ts_sec/ts_usec |
| Формат времени | pcap timestamp seconds + micro/nanoseconds |
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
- TCP/UDP ports, TCP flags;
- DNS/LDAP/SMB/DCERPC indicators после parser;
- host + network correlation по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | pcap headers доступны |
| Нестабильная структура | нет | classic pcap magic/header стабилен |
| Смешанные схемы | нет | один binary capture format |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
`.cap` полезен для network/hybrid feature extraction, но для production pipeline нужен отдельный pcap parser или библиотека вроде Scapy/tshark. Исходные VALIDATION файлы не изменялись.
"""

        return f"""# Format Analysis: cap

## 1. Purpose
`.cap` in Host VALIDATION contains classic pcap packet capture files for network attack scenarios. The format is useful for network/hybrid feature extraction, but full extraction requires a dedicated packet parser.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | cap |
| Extension variants | .cap |
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
| Header | pcap global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Content Structure
Files contain packet metadata and payload bytes in a classic pcap container. The sample contains Ethernet/IPv4 packets; IP protocol distribution: {protocols}. File names identify attack scenarios and can be used as external context, but there is no embedded label field.

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
| Field name | packet header ts_sec/ts_usec |
| Time format | pcap timestamp seconds + micro/nanoseconds |
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
| Missing values | no | pcap headers are available |
| Unstable structure | no | classic pcap magic/header is stable |
| Mixed schemas | no | one binary capture format |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
`.cap` is useful for network/hybrid feature extraction, but a dedicated pcap parser or Scapy/tshark-like tooling is required for the production pipeline. Source VALIDATION files were not modified.
"""

    @staticmethod
    def _fields_table(summary: dict[str, Any], language: str) -> str:
        labels = {
            "magic": "pcap signature",
            "version": "pcap version",
            "snaplen": "capture snap length",
            "network": "link-layer type",
            "ip_protocol": "IP protocol",
            "tcp_dst_port": "sample TCP destination port",
            "udp_dst_port": "sample UDP destination port",
        }
        first_probe = summary["file_probes"][0] if summary["file_probes"] else {}
        rows = [
            ("magic", "hex", labels["magic"], first_probe.get("magic", "")),
            ("version", "string", labels["version"], first_probe.get("version", "")),
            ("snaplen", "integer", labels["snaplen"], first_probe.get("snaplen", "")),
            ("network", "integer", labels["network"], first_probe.get("network", "")),
            ("ip_protocol", "integer", labels["ip_protocol"], next(iter(summary["ip_protocols"]), "")),
            ("tcp_dst_port", "integer", labels["tcp_dst_port"], next(iter(summary["tcp_ports_sample"]), "")),
            ("udp_dst_port", "integer", labels["udp_dst_port"], next(iter(summary["udp_ports_sample"]), "")),
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
        status_by_format = {"cap": (summary["final_status"], "cap.md")}
        rows = []
        for fmt, count in sorted(self._load_host_validation_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task1: Analysis of host validation cap dataset files"
            if ru
            else "# Task1 Report: Analysis of host validation cap dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\cap` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\cap` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_cap_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/cap.md`
- `docs/en/analysis-dataset/host/validation/cap.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task1(Analysis of host validation cap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task1(Analysis of host validation cap dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.cap`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler сортирует пути, берёт равномерную выборку и читает только pcap headers + ограниченное число packets.' if ru else 'The handler sorts paths, takes an even sample, and reads only pcap headers plus a limited number of packets.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_host_validation_format_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}
        return {fmt: len(paths) for fmt, paths in role_bucket.items() if isinstance(paths, list)}

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "parsed_packets": summary["parsed_packets"],
            "ip_protocols": summary["ip_protocols"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
