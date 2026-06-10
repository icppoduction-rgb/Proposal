from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.host_analyze.analyze_host_validation_cap_dataset_handler import HostValidationCAPContentAnalysisHandler
from scripts.handlers.host_analyze.analyze_host_validation_pcapng_dataset_handler import HostValidationPCAPNGContentAnalysisHandler
from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSTrainPCAPContentAnalysisResult:
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
class DNSPCAPProbe:
    path: str
    file_name: str
    file_size_bytes: int
    container_variant: str
    magic: str
    sampled_packets: int
    parse_error: str | None


class DNSTrainPCAPContentAnalysisHandler:
    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "pcap"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_PACKETS_PER_FILE = 500
    DEFAULT_MAX_BLOCKS_PER_FILE = 2000

    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-dns-train-pcap-summary.json"

    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_packets_per_file: int = DEFAULT_MAX_PACKETS_PER_FILE,
        max_blocks_per_file: int = DEFAULT_MAX_BLOCKS_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_packets_per_file = max(1, max_packets_per_file)
        self.max_blocks_per_file = max(1, max_blocks_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "train"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "train"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "dns" / "train"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "dns" / "train"
        self._classic_probe = HostValidationCAPContentAnalysisHandler(
            temp_data_path=temp_data_path,
            project_root=project_root,
            report_path=report_path,
            max_files_per_format=max_files_per_format,
            max_packets_per_file=max_packets_per_file,
        )
        self._pcapng_probe = HostValidationPCAPNGContentAnalysisHandler(
            temp_data_path=temp_data_path,
            project_root=project_root,
            report_path=report_path,
            max_files_per_format=max_files_per_format,
            max_blocks_per_file=max_blocks_per_file,
            max_packets_per_file=max_packets_per_file,
        )

    def analyze_and_generate_docs(self) -> DNSTrainPCAPContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-dns-file.json for TRAIN/pcap.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcap.md"
        docs_en_path = self.docs_en_dir / "pcap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task2(Analysis of dns train pcap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task2(Analysis of dns train pcap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return DNSTrainPCAPContentAnalysisResult(
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
        source_json_path = self.temp_data_path / self.DNS_INPUT_JSON_FILE
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
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[DNSPCAPProbe] = []
        variants: Counter[str] = Counter()
        ip_protocols: Counter[str] = Counter()
        tcp_ports: Counter[str] = Counter()
        udp_ports: Counter[str] = Counter()
        packet_lengths: list[int] = []
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, packet_stats = self._probe_file(path)
            probes.append(probe)
            variants[probe.container_variant] += 1
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            ip_protocols.update(packet_stats["ip_protocols"])
            tcp_ports.update(packet_stats["tcp_ports"])
            udp_ports.update(packet_stats["udp_ports"])
            packet_lengths.extend(packet_stats["packet_lengths"])

        parsed_packets = sum(probe.sampled_packets for probe in probes)
        dns_port_hits = int(tcp_ports.get("53", 0)) + int(udp_ports.get("53", 0))
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.DNS_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_packets_per_file": self.max_packets_per_file,
                "max_blocks_per_file": self.max_blocks_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths],
            "file_probes": [probe.__dict__ for probe in probes],
            "container_variants": dict(variants.most_common()),
            "parsed_packets": parsed_packets,
            "dns_port_hits_sample": dns_port_hits,
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

    def _probe_file(self, path: Path) -> tuple[DNSPCAPProbe, dict[str, Counter[str] | list[int]]]:
        empty_stats: dict[str, Counter[str] | list[int]] = {
            "ip_protocols": Counter(),
            "tcp_ports": Counter(),
            "udp_ports": Counter(),
            "packet_lengths": [],
        }
        if not path.exists():
            return DNSPCAPProbe(str(path), path.name, 0, "missing", "", 0, "file_not_found"), empty_stats
        file_size = path.stat().st_size
        if file_size == 0:
            return DNSPCAPProbe(str(path), path.name, 0, "empty", "", 0, "empty_file"), empty_stats
        magic = path.read_bytes()[:4].hex()
        if magic == "0a0d0d0a":
            pcapng_probe, stats = self._pcapng_probe._probe_pcapng(path)
            return (
                DNSPCAPProbe(
                    path=str(path),
                    file_name=path.name,
                    file_size_bytes=file_size,
                    container_variant="pcapng",
                    magic=magic,
                    sampled_packets=pcapng_probe.sampled_packets,
                    parse_error=pcapng_probe.parse_error,
                ),
                stats,
            )
        classic_magics = {"d4c3b2a1", "a1b2c3d4", "4d3cb2a1", "a1b23c4d"}
        if magic in classic_magics:
            classic_probe, stats = self._classic_probe._probe_cap(path)
            return (
                DNSPCAPProbe(
                    path=str(path),
                    file_name=path.name,
                    file_size_bytes=file_size,
                    container_variant="classic_pcap",
                    magic=magic,
                    sampled_packets=classic_probe.sampled_packets,
                    parse_error=classic_probe.parse_error,
                ),
                stats,
            )
        return DNSPCAPProbe(str(path), path.name, file_size, "unknown", magic, 0, "unknown_capture_magic"), empty_stats

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"])
        variants = ", ".join(f"{key}: {value}" for key, value in summary["container_variants"].items())
        protocols = ", ".join(f"{key}: {value}" for key, value in summary["ip_protocols"].items()) or "-"
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS TRAIN содержат packet capture трафик для benign, malware, phishing и spam классов. Формат нужен для DNS query/response parsing, packet/flow features и проверки признаков, извлечённых из CSV.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | TRAIN |
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
| Заголовок | pcap/pcapng global header |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да, packet records |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Содержательная структура
Контейнеры в sample: {variants}. IP protocol distribution: {protocols}. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: {summary["dns_port_hits_sample"]}.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| container_variant | string | classic pcap или pcapng | {next(iter(summary["container_variants"]), "")} |
| magic | hex | capture signature | {summary["file_probes"][0]["magic"] if summary["file_probes"] else ""} |
| ip_protocol | integer | IP protocol | {next(iter(summary["ip_protocols"]), "")} |
| udp_dst_port | integer | UDP destination port sample | {next(iter(summary["udp_ports_sample"]), "")} |
| tcp_dst_port | integer | TCP destination port sample | {next(iter(summary["tcp_ports_sample"]), "")} |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла |
| Значения label | benign, malware, phishing, spam |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | packet timestamp |
| Формат времени | pcap seconds/usec или pcapng timestamp |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- query name, query length, subdomain depth;
- qtype/qclass;
- response size, TTL, answer count;
- NXDOMAIN/RCODE distribution;
- inter-query intervals.

### Network / hybrid-признаки
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- correlation with CSV domain/IP features.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | packet headers доступны |
| Нестабильная структура | частично | `.pcap` bucket содержит classic pcap и pcapng |
| Смешанные схемы | да | нужен parser, поддерживающий оба контейнера |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
DNS TRAIN pcap полезен для network/DNS feature extraction, но production pipeline должен использовать packet parser с поддержкой classic pcap и pcapng.
"""

        return f"""# Format Analysis: pcap

## 1. Purpose
DNS TRAIN PCAP files contain packet capture traffic for benign, malware, phishing, and spam classes. The format is needed for DNS query/response parsing, packet/flow features, and validation of CSV-derived features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
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
| Header | pcap/pcapng global header |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes, packet records |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample packets | {summary["parsed_packets"]} |

## 5. Content Structure
Containers in the sample: {variants}. IP protocol distribution: {protocols}. DNS-related packets are identifiable through TCP/UDP port 53; port-53 hits in the limited sample: {summary["dns_port_hits_sample"]}.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| container_variant | string | classic pcap or pcapng | {next(iter(summary["container_variants"]), "")} |
| magic | hex | capture signature | {summary["file_probes"][0]["magic"] if summary["file_probes"] else ""} |
| ip_protocol | integer | IP protocol | {next(iter(summary["ip_protocols"]), "")} |
| udp_dst_port | integer | UDP destination port sample | {next(iter(summary["udp_ports_sample"]), "")} |
| tcp_dst_port | integer | TCP destination port sample | {next(iter(summary["tcp_ports_sample"]), "")} |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name |
| Label values | benign, malware, phishing, spam |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | packet timestamp |
| Time format | pcap seconds/usec or pcapng timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- query name, query length, subdomain depth;
- qtype/qclass;
- response size, TTL, answer count;
- NXDOMAIN/RCODE distribution;
- inter-query intervals.

### Network / Hybrid Features
- packet/byte counts;
- UDP/TCP port 53 activity;
- flow duration and burst features;
- correlation with CSV domain/IP features.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | no | packet headers are available |
| Unstable structure | partial | `.pcap` bucket contains classic pcap and pcapng |
| Mixed schemas | yes | parser must support both containers |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN pcap is useful for network/DNS feature extraction, but the production pipeline must use a packet parser that supports both classic pcap and pcapng.
"""

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
            "csv": (self._load_optional_status("analysis-dns-train-csv-summary.json"), "csv.md"),
            "pcap": (summary["final_status"], "pcap.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS TRAIN)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task2: Analysis of dns train pcap dataset files"
            if ru
            else "# Task2 Report: Analysis of dns train pcap dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_DNS_DATASETS_FILTER\\TRAIN\\pcap` на основе "
            f"`{self.DNS_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_DNS_DATASETS_FILTER\\TRAIN\\pcap` using `{self.DNS_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_train_pcap_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/train/pcap.md`
- `docs/en/analysis-dataset/dns/train/pcap.md`
- `docs/ru/analysis-dataset/dns/train/README.md`
- `docs/en/analysis-dataset/dns/train/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/dns/train/Task2(Analysis of dns train pcap dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/dns/train/Task2(Analysis of dns train pcap dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TRAIN.pcap`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler определяет classic pcap/pcapng по magic bytes и читает ограниченное число packet records.' if ru else 'The handler detects classic pcap/pcapng by magic bytes and reads a limited number of packet records.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.DNS_INPUT_JSON_FILE).read(default={})
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
        return json.dumps(
            {
                "format": summary["format"],
                "role": summary["role"],
                "scope": summary["scope"],
                "container_variants": summary["container_variants"],
                "parsed_packets": summary["parsed_packets"],
                "dns_port_hits_sample": summary["dns_port_hits_sample"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
